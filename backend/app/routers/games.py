from fastapi import APIRouter, Depends, HTTPException, Response
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List
import asyncio
import io

from app.core.database import get_db
from app.models.schemas import (
    GameMeta, GameSettings, GameMemberDoc, GameChapterDoc,
    GameMessageDoc, GameActionDoc
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/games", tags=["games"])


# Collection helpers

def _rooms(db):
    return db["rooms"]


def _games(db):
    return db["games"]


def _game_members(db):
    return db["game_members"]


def _game_chapters(db):
    return db["game_chapters"]


def _game_messages(db):
    return db["game_messages"]


def _game_actions(db):
    return db["game_actions"]

def _users(db):
    return db["users"]

async def _broadcast_game(db, game_id: str, message: dict):
    # Reutilizar manager de websockets por canal game:{game_id}
    try:
        from .websockets import manager
        await manager.broadcast_to_room(message, f"game:{game_id}")
    except Exception:
        pass

async def open_action_phase(db, game: dict):
    """Abre la fase de acciones y emite evento WS."""
    settings = game.get("settings", {})
    seconds = int(settings.get("discussion_time", 60) or 60)
    ends_at = datetime.utcnow() + timedelta(seconds=seconds)
    
    print(f"[open_action_phase] Opening phase with {seconds}s, ends_at={ends_at.isoformat()}")
    
    await _games(db).update_one(
        {"_id": game["_id"]},
        {"$set": {
            "game_state": "action_phase",
            "action_phase": {
                "open": True,
                "started_at": datetime.utcnow().isoformat(),
                "ends_at": ends_at.isoformat(),
                "seconds_total": seconds,
            },
            "continue_ready": []
        }}
    )
    
    await _broadcast_game(db, str(game["_id"]), {
        "type": "game:action_phase_started",
        "data": {
            "ends_at": ends_at.isoformat(),
            "seconds_total": seconds,
            "auto_continue": bool(settings.get("auto_continue", False))
        }
    })
    
    # Iniciar el timer del manager
    try:
        from .websockets import manager
        await manager.schedule_action_phase_timer(str(game["_id"]), ends_at.isoformat(), db)
    except Exception as e:
        print(f"Error starting action phase timer: {e}")

async def _open_action_phase_idempotent(db, game_id: ObjectId, expected_chapter: int) -> bool:
    """Helper idempotente para abrir action_phase desde estado playing."""
    try:
        game = await _games(db).find_one({"_id": game_id})
        if not game:
            return False
            
        settings = game.get("settings", {})
        seconds = int(settings.get("discussion_time", 300) or 300)
        ends_at = datetime.utcnow() + timedelta(seconds=seconds)
        
        print(f"[_open_action_phase_idempotent] Attempting to open action phase for game {game_id}, chapter {expected_chapter}")
        
        res = await _games(db).update_one(
            {
                "_id": game_id, 
                "game_state": "playing", 
                "current_chapter": expected_chapter
            },
            {
                "$set": {
                    "game_state": "action_phase",
                    "action_phase": {
                        "open": True,
                        "started_at": datetime.utcnow().isoformat(),
                        "ends_at": ends_at.isoformat(),
                        "seconds_total": seconds,
                    },
                    "continue_ready": []
                }
            }
        )
        
        if res.modified_count == 0:
            print(f"[_open_action_phase_idempotent] Action phase already open or conditions not met for game {game_id}")
            return False
        
        print(f"[_open_action_phase_idempotent] Action phase opened successfully for game {game_id}")
        
        # Broadcast phase change
        await _broadcast_game(db, str(game_id), {
            "type": "game:action_phase_started",
            "data": {
                "ends_at": ends_at.isoformat(),
                "seconds_total": seconds,
                "auto_continue": bool(settings.get("auto_continue", False))
            }
        })
        
        # Programa timer
        try:
            from .websockets import manager
            await manager.schedule_action_phase_timer(str(game_id), ends_at.isoformat(), db)
            print(f"[_open_action_phase_idempotent] Timer scheduled for action phase")
        except Exception as timer_err:
            print(f"[_open_action_phase_idempotent] Error scheduling timer: {timer_err}")
        
        return True
        
    except Exception as e:
        print(f"[_open_action_phase_idempotent] Error: {e}")
        return False

async def _finalize_actions_and_generate_next(db, game_id: ObjectId, expected_chapter: int | None = None):
    """Cierra la fase de acciones y genera el siguiente capítulo."""
    try:
        print(f"[finalize] Attempting to close action phase for game {game_id}")

        # Si no pasaron expected_chapter, leerlo una vez (pero mejor pasarlo desde los triggers)
        if expected_chapter is None:
            doc = await _games(db).find_one({"_id": game_id}, {"current_chapter": 1, "game_state": 1})
            if not doc or doc.get("game_state") != "action_phase":
                return
            expected_chapter = int(doc.get("current_chapter") or 0)

        # Small debounce: if action_phase was opened very recently, wait a short moment
        try:
            cur = await _games(db).find_one({"_id": game_id}, {"action_phase.started_at": 1, "game_state": 1, "current_chapter": 1})
            if cur and cur.get("game_state") == "action_phase":
                started_at_iso = (cur.get("action_phase") or {}).get("started_at")
                if started_at_iso:
                    try:
                        started_at = datetime.fromisoformat(started_at_iso)
                        delta = (datetime.utcnow() - started_at).total_seconds()
                        # Si la fase se abrió hace menos de 1s, esperar el resto
                        if delta < 1.0:
                            wait = 1.0 - delta
                            print(f"[finalize] Debounce: waiting {wait:.2f}s before attempting finalize for game {game_id}")
                            await asyncio.sleep(wait)
                    except Exception:
                        pass
        except Exception:
            pass

        # Lock + idempotencia por capítulo + marcar "closing" inmediatamente
        res = await _games(db).update_one(
            {
                "_id": game_id,
                "advancing": {"$ne": True},
                "game_state": "action_phase",
                "current_chapter": expected_chapter,  # 🔒 solo cerrar la fase de ESTE capítulo
            },
            {"$set": {"advancing": True, "game_state": "closing"}},  # ← marcar closing inmediatamente
        )
        if res.modified_count == 0:
            print(f"[finalize] Phase already closing/changed for game {game_id}, skipping")
            return

        print(f"[finalize] Lock acquired and marked as closing, generating next chapter for game {game_id}")
        
        # Broadcast inmediato que estamos generando
        await _broadcast_game(db, str(game_id), {
            "type": "game:phase_changed",
            "data": {"phase": "closing", "message": "Escribiendo el capítulo..."}
        })
        
        try:
            await advance_to_next_chapter(db, str(game_id))
        finally:
            await _games(db).update_one({"_id": game_id}, {"$unset": {"advancing": ""}})
            print(f"[finalize] Lock released for game {game_id}")
        
    except Exception as e:
        print(f"Error in _finalize_actions_and_generate_next: {e}")
        # Asegurar que el lock se libere en caso de error
        try:
            await _games(db).update_one(
                {"_id": game_id}, 
                {"$unset": {"advancing": ""}}
            )
        except:
            pass


async def maybe_open_actions_or_continue(db, game: dict):
    """DEPRECATED: Ahora la transición playing -> action_phase se maneja via POST /games/{id}/continue"""
    print(f"[maybe_open_actions_or_continue] DEPRECATED: Use POST /games/{{id}}/continue for phase transitions")
    pass

async def advance_to_next_chapter(db, game_id: str):
    """Genera el siguiente capítulo usando IA"""
    try:
        print(f"[advance] Starting chapter generation for game {game_id}")
        game = await _games(db).find_one({"_id": ObjectId(game_id)})
        if not game:
            print(f"[advance] Game {game_id} not found")
            return
        
        # Guardas tempranas: verificar si ya terminó o llegó al máximo
        max_chapters = int(game.get("max_chapters", 5) or 5)
        current_chapter = int(game.get("current_chapter", 0) or 0)
        if game.get("game_state") == "finished" or current_chapter >= max_chapters:
            print(f"[advance] Already finished or at max chapters (cur={current_chapter}, max={max_chapters}), skipping")
            return
        
        print(f"[advance] Current chapter: {current_chapter}")
        
        # Recolectar contexto
        prev = []
        async for ch in _game_chapters(db).find({"game_id": game_id}).sort("chapter_number", 1):
            prev.append(ch.get("content", ""))
        
        # Cargar mundo y personajes
        world = {}
        characters = []
        try:
            room_id = game.get("room_id")
            if room_id:
                room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
                if room:
                    if room.get("world_id"):
                        w = await db["worlds"].find_one({"_id": ObjectId(room["world_id"])})
                        world = w or {}
                    # Extraer solo los datos de personajes de selected_characters
                    selected_chars = room.get("selected_characters", []) or []
                    characters = [sc.get("character", {}) for sc in selected_chars if sc.get("character")]
                    print(f"[advance] Extracted {len(characters)} characters from {len(selected_chars)} selections")
        except Exception:
            pass
        
        # Acciones pendientes del capítulo actual
        pending = [a async for a in _game_actions(db).find({
            "game_id": game_id,
            "chapter_number": current_chapter,
            "status": {"$in": ["pending", "approved"]}
        }).sort("created_at", 1)]
        
        print(f"[advance] Found {len(pending)} pending actions")
        
        # Generar nuevo capítulo con estructura narrativa
        from app.services.ai_service import AIService
        ai = AIService()
        new_num = current_chapter + 1
        if pending:
            text = await ai.generate_chapter_with_actions(
                world=world or {}, 
                previous_chapters=prev, 
                player_actions=pending, 
                characters=characters,
                total_chapters=max_chapters,
                chapter_index=new_num
            )
        else:
            text = await ai.generate_chapter_automatic(
                world=world or {}, 
                previous_chapters=prev, 
                characters=characters,
                total_chapters=max_chapters,
                chapter_index=new_num
            )
        
        print(f"[advance] Generated chapter text ({len(text)} chars)")
        
        await _game_chapters(db).insert_one({
            "game_id": game_id,
            "chapter_number": new_num,
            "content": text,
            "created_at": datetime.utcnow().isoformat(),
        })
        
        print(f"[advance] Inserted chapter {new_num}, updating game state")
        
        # Actualizar juego y limpiar phase/advancing
        max_chapters = game.get("max_chapters", 5)
        if new_num >= max_chapters:
            print(f"[advance] Game finished, updating to chapter {new_num}")
            await _games(db).update_one(
                {"_id": ObjectId(game_id)}, 
                {
                    "$set": {
                        "current_chapter": new_num, 
                        "game_state": "finished",
                        "finished_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                    "$unset": {
                        "action_phase": "",
                        "continue_ready": "",
                        "advancing": ""
                    }
                }
            )
            
            # ✅ Broadcast de juego terminado
            await _broadcast_game(db, game_id, {
                "type": "game:state_changed",
                "data": {"state": "finished"}
            })
            await _broadcast_game(db, game_id, {
                "type": "game:finished",
                "data": {"game_id": game_id}
            })
        else:
            # ✅ Abrir directamente la fase de acciones del nuevo capítulo
            print(f"[advance] Game continues, opening action_phase for chapter {new_num}")
            
            settings = game.get("settings", {})
            discussion_seconds = int(settings.get("discussion_time", 300) or 300)
            ends_at = datetime.utcnow() + timedelta(seconds=discussion_seconds)
            
            await _games(db).update_one(
                {"_id": ObjectId(game_id)}, 
                {
                    "$set": {
                        "current_chapter": new_num, 
                        "game_state": "action_phase",  # ← abrir fase de acciones YA
                        "action_phase": {
                            "open": True,
                            "started_at": datetime.utcnow().isoformat(),
                            "ends_at": ends_at.isoformat(),
                            "seconds_total": discussion_seconds,
                        },
                        "continue_ready": [],
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                    "$unset": {
                        "advancing": ""
                    }
                }
            )
            
            # Obtener miembros para broadcast
            members = [m async for m in _game_members(db).find({"game_id": game_id})]
            total_members = len(members)
            
            # Orden de broadcasts: 1) capítulo creado, 2) fase cambiada, 3) listos reseteados
            print(f"[advance] Broadcasting chapter_created event")
            await _broadcast_game(db, game_id, {
                "type": "game:chapter_created",
                "data": {
                    "chapter_number": new_num,
                    "discussion_seconds": discussion_seconds
                }
            })
            
            print(f"[advance] Broadcasting action_phase_started event")
            await _broadcast_game(db, game_id, {
                "type": "game:action_phase_started",
                "data": {
                    "ends_at": ends_at.isoformat(),
                    "seconds_total": discussion_seconds,
                    "auto_continue": bool(settings.get("auto_continue", False))
                }
            })
            
            await _broadcast_game(db, game_id, {
                "type": "game:phase_changed",
                "data": {"phase": "action_phase"}
            })
            
            await _broadcast_game(db, game_id, {
                "type": "game:continue_update",
                "data": {
                    "ready_count": 0,
                    "total": total_members,
                    "remaining_seconds": discussion_seconds
                }
            })
            
            # Programar timer
            try:
                from .websockets import manager
                await manager.schedule_action_phase_timer(str(game_id), ends_at.isoformat(), db)
                print(f"[advance] Timer scheduled for action phase")
            except Exception as timer_err:
                print(f"[advance] Error scheduling timer: {timer_err}")
        
        print(f"[advance] Game state updated successfully")
        
        # Archivar acciones del capítulo anterior
        try:
            await _game_actions(db).update_many(
                {"game_id": game_id, "chapter_number": current_chapter, "status": "pending"}, 
                {"$set": {"status": "approved"}}
            )
            print(f"[advance] Actions archived for chapter {current_chapter}")
        except Exception as e:
            print(f"[advance] Error archiving actions: {e}")
            
    except Exception as e:
        print(f"Error in advance_to_next_chapter: {e}")


async def _create_complete_game_from_room(db, room_id: str) -> str:
    """Función interna para crear un Game completo con primer capítulo generado por IA.
    Esta es la lógica centralizada que se usa tanto desde WebSocket como desde HTTP.
    """
    try:
        room_oid = ObjectId(room_id)
    except Exception:
        raise ValueError("Formato de ID inválido")

    room = await _rooms(db).find_one({"_id": room_oid})
    if not room:
        raise ValueError("Sala no encontrada")

    member_ids = room.get("member_ids", []) or []
    ready_players = set(room.get("ready_players", []) or [])
    if not member_ids or any(mid not in ready_players for mid in member_ids):
        raise ValueError("No todos los jugadores están listos")

    settings = GameSettings(
        allow_suggestions=room.get("allow_actions", room.get("allow_suggestions", True)),
        discussion_time=int(room.get("discussion_time", 300) or 300),
        auto_continue=bool(room.get("auto_continue", False)),
        continue_time=int(room.get("continue_time", 60) or 60),
    )

    game_doc = {
        "room_id": str(room.get("_id")),
        "name": room.get("name"),
        "world_id": str(room.get("world_id") or ""),
        "max_chapters": int(room.get("max_chapters", 5) or 5),
        "max_players": int(room.get("max_players", 4) or 4),
        "settings": settings.model_dump(),
        "owner_id": room.get("owner_id") or room.get("admin_id"),
        "admin_id": room.get("admin_id"),
        "current_chapter": 0,  # ✅ Comenzamos en 0, se incrementará a 1 en background
        "game_state": "initializing",  # ✅ Estado temporal hasta que se genere el primer capítulo
        "created_at": datetime.utcnow().isoformat(),
    }
    res = await _games(db).insert_one(game_doc)
    game_id = res.inserted_id

    # Crear miembros del juego
    members = room.get("members", []) or []
    if not members:
        members = [{"user_id": mid, "username": None, "is_ready": True} for mid in member_ids]

    bulk_members = []
    for m in members:
        uid = str(m.get("user_id") or m)
        bulk_members.append({
            "game_id": str(game_id),
            "user_id": uid,
            "character_id": m.get("selected_character_id") or None,
            "role": "admin" if uid == room.get("admin_id") else "player",
            "joined_at": datetime.utcnow().isoformat(),
            "is_ready": True,
        })
    if bulk_members:
        await _game_members(db).insert_many(bulk_members)

    # ✅ Marcar la room como closing (no borrar aún)
    await _rooms(db).update_one(
        {"_id": room_oid},
        {"$set": {"game_state": "closing", "game_id": str(game_id), "status": "closing"}}
    )

    # 🚀 GENERAR PRIMER CAPÍTULO EN BACKGROUND (no bloquear respuesta)
    async def _initialize_game():
        try:
            print(f"[init_game] Starting background initialization for game {game_id}")
            
            # Cargar mundo y personajes para el contexto de IA
            world = {}
            characters = []
            try:
                world_id = room.get("world_id")
                if world_id:
                    world = await db["worlds"].find_one({"_id": ObjectId(world_id)}) or {}
                characters = room.get("selected_characters", []) or []
            except Exception:
                pass

            # Generar primer capítulo
            from app.services.ai_service import AIService
            ai_service = AIService()
            first_chapter_text = await ai_service.generate_first_chapter(
                world=world,
                characters=characters
            )

            # Guardar el capítulo en game_chapters
            await _game_chapters(db).insert_one({
                "game_id": str(game_id),
                "chapter_number": 1,
                "content": first_chapter_text,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": room.get("admin_id"),
            })

            # Actualizar game a action_phase con capítulo 1
            settings = room.get("settings", {}) or {}
            discussion_seconds = int(settings.get("discussion_time", 300) or 300)
            ends_at = datetime.utcnow() + timedelta(seconds=discussion_seconds)
            
            await _games(db).update_one(
                {"_id": game_id},
                {"$set": {
                    "current_chapter": 1,
                    "game_state": "action_phase",  # ← abrir directamente en action_phase
                    "action_phase": {
                        "open": True,
                        "started_at": datetime.utcnow().isoformat(),
                        "ends_at": ends_at.isoformat(),
                        "seconds_total": discussion_seconds,
                    },
                    "continue_ready": [],
                    "updated_at": datetime.utcnow().isoformat(),
                }}
            )

            print(f"[init_game] First chapter generated for game {game_id}")

            # Broadcast que el juego ha iniciado
            from .websockets import manager
            await manager.broadcast_to_room({
                "type": "game_started",
                "data": {"game_id": str(game_id)}
            }, f"room:{room_id}")

            # Broadcast del primer capítulo y apertura de action_phase
            await _broadcast_game(db, str(game_id), {
                "type": "game:chapter_created",
                "data": {
                    "chapter_number": 1,
                    "discussion_seconds": discussion_seconds
                }
            })
            
            await _broadcast_game(db, str(game_id), {
                "type": "game:action_phase_started",
                "data": {
                    "ends_at": ends_at.isoformat(),
                    "seconds_total": discussion_seconds,
                    "auto_continue": bool(settings.get("auto_continue", False))
                }
            })
            
            await _broadcast_game(db, str(game_id), {
                "type": "game:phase_changed",
                "data": {"phase": "action_phase"}
            })

            # ✅ Programar timer para la primera fase de acciones
            try:
                await manager.schedule_action_phase_timer(str(game_id), ends_at.isoformat(), db)
                print(f"[init_game] Timer scheduled for first action phase")
            except Exception as timer_err:
                print(f"[init_game] Error scheduling timer: {timer_err}")
            
            print(f"[init_game] Game {game_id} ready with first action phase open.")

        except Exception as e:
            print(f"[init_game] Error during background initialization: {e}")
            # Si falla la generación, marcar el juego como fallido
            await _games(db).update_one(
                {"_id": game_id}, 
                {"$set": {"game_state": "failed", "error": str(e)}}
            )

    # Ejecutar en background
    import asyncio
    asyncio.create_task(_initialize_game())

    return str(game_id)


@router.post("/from-room/{room_id}", response_model=GameMeta)
async def create_game_from_room(room_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Crear un Game normalizado desde una Room cuando todos están listos.
    Copia settings y miembros, y marca la Room como started.
    """
    try:
        room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
        if not room:
            raise HTTPException(status_code=404, detail="Sala no encontrada")

        # Solo admin puede iniciar
        if str(current_user["_id"]) != room.get("admin_id"):
            raise HTTPException(status_code=403, detail="Solo el admin puede iniciar la partida")

        # Usar la función centralizada
        game_id = await _create_complete_game_from_room(db, room_id)
        
        # Obtener el juego creado para la respuesta
        created = await _games(db).find_one({"_id": ObjectId(game_id)})
        created["_id"] = str(created["_id"])
        
        # Normalizar IDs para response model
        for k in ["room_id", "world_id", "owner_id", "admin_id"]:
            if k in created and created[k] is not None:
                created[k] = str(created[k])
        
        return created

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in create_game_from_room: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/{game_id}/leave")
async def leave_game(game_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Salir del juego (remover de game_members)"""
    try:
        gid = ObjectId(game_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de ID inválido")

    game = await _games(db).find_one({"_id": gid})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")

    user_id = str(current_user["_id"])
    
    # Remover de game_members
    await _game_members(db).delete_many({"game_id": game_id, "user_id": user_id})
    
    # Remover de continue_ready si estaba listo
    await _games(db).update_one({"_id": gid}, {"$pull": {"continue_ready": user_id}})
    
    return {"ok": True, "message": "Has salido del juego"}


@router.get("/my")
async def my_games(db=Depends(get_db), user=Depends(get_current_user)):
    """Obtener todas las partidas en las que participa el usuario."""
    uid = str(user["_id"])
    game_ids = [gm["game_id"] async for gm in _game_members(db).find({"user_id": uid}, {"game_id": 1, "_id": 0})]
    oids = [ObjectId(g) for g in game_ids if ObjectId.is_valid(g)]
    games = []
    async for g in _games(db).find({"_id": {"$in": oids}}):
        g["_id"] = str(g["_id"])
        games.append(g)
    return games


@router.get("/{game_id}", response_model=GameMeta)
async def get_game(game_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    try:
        gid = ObjectId(game_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de ID inválido")
    game = await _games(db).find_one({"_id": gid})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")
    # Backward-compat: ensure owner_id present
    if not game.get("owner_id"):
        game["owner_id"] = game.get("admin_id")
    game["_id"] = str(game["_id"]) 
    for k in ["room_id", "world_id", "owner_id", "admin_id"]:
        if k in game and game[k] is not None:
            game[k] = str(game[k])
    return game


@router.post("/{game_id}/continue")
async def mark_continue(game_id: str, payload: dict | None = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Jugador marca listo/no listo para continuar. Solo funciona en action_phase."""
    try:
        gid = ObjectId(game_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de ID inválido")

    game = await _games(db).find_one({"_id": gid})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")

    game_state = game.get("game_state")
    current_chapter = int(game.get("current_chapter", 0) or 0)
    user_id = str(current_user["_id"])
    ready = bool((payload or {}).get("ready", True))

    # ✅ Solo permitir continue en action_phase
    if game_state == "closing":
        raise HTTPException(status_code=409, detail="No se puede marcar listo mientras se genera el capítulo. Espera a que termine.")
    
    elif game_state != "action_phase":
        raise HTTPException(status_code=409, detail=f"No se puede continuar en estado {game_state}")

    # Manejar fase de acciones
    if game_state == "action_phase":
        phase = game.get("action_phase") or {}
        
        # Actualizar lista de ready
        ready_set = set(str(x) for x in (game.get("continue_ready", []) or []))
        if ready:
            ready_set.add(user_id)
        else:
            ready_set.discard(user_id)

        # Persistir cambios
        await _games(db).update_one({"_id": gid}, {"$set": {"continue_ready": list(ready_set)}})

        # Obtener miembros y métricas
        members = [m async for m in _game_members(db).find({"game_id": game_id})]
        total = len(members)
        ready_count = len(ready_set)

        # Calcular remaining_seconds usando phase para cubrir desajustes
        remaining_seconds = 0
        time_over = False
        ends_at_iso = phase.get("ends_at")
        if ends_at_iso:
            try:
                ends_at = datetime.fromisoformat(ends_at_iso)
                remaining_seconds = max(0, int((ends_at - datetime.utcnow()).total_seconds()))
                # ✅ Borde de milisegundos: si ya está en 0, trátalo como terminado
                time_over = (remaining_seconds <= 0) or (datetime.utcnow() >= ends_at)
            except Exception:
                pass

        # Debug logs
        print(f"[continue] game_state={game_state}, ready_count={ready_count}/{total}, require_all={game.get('settings', {}).get('require_all_players', True)}, remaining_seconds={remaining_seconds}, time_over={time_over}")

        # Emitir update inmediato
        await _broadcast_game(db, game_id, {
            "type": "game:continue_update",
            "data": {
                "ready_count": ready_count,
                "total": total,
                "remaining_seconds": remaining_seconds
            }
        })

        # Verificar condiciones para cerrar la fase
        settings = game.get("settings", {})
        require_all = settings.get("require_all_players", True)
        
        everyone_ready = require_all and ready_count == total and total > 0
        reached_threshold = (not require_all) and ready_count >= max(1, int(total * 0.6))

        if everyone_ready or reached_threshold or time_over:
            # cancelar timer de la fase actual
            try:
                from .websockets import manager
                task = manager.action_phase_tasks.get(str(gid))
                if task:
                    task.cancel()
                manager.action_phase_tasks.pop(str(gid), None)
            except Exception:
                pass

            # encolar finalize idempotente por capítulo
            asyncio.create_task(_finalize_actions_and_generate_next(db, gid, expected_chapter=current_chapter))

        return {"ok": True}


@router.get("/{game_id}/members", response_model=List[GameMemberDoc])
async def list_members(game_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    items = []
    async for it in _game_members(db).find({"game_id": game_id}):
        it["_id"] = str(it.get("_id"))
        items.append(it)
    return items


@router.post("/{game_id}/messages", response_model=GameMessageDoc)
async def post_message(game_id: str, payload: GameMessageDoc, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Obtener username del usuario
    user_name = current_user.get("username", "")
    
    doc = payload.model_dump(by_alias=True)
    doc.update({
        "game_id": game_id,
        "user_id": str(current_user["_id"]),
        "username": user_name,
        "timestamp": datetime.utcnow().isoformat(),
    })
    res = await _game_messages(db).insert_one(doc)
    created = await _game_messages(db).find_one({"_id": res.inserted_id})
    created["_id"] = str(created["_id"])

    # ✅ Difundir a todos los clientes suscritos al canal del juego
    await _broadcast_game(db, game_id, {
        "type": "game:new_message",
        "data": created,
    })

    return created


@router.get("/{game_id}/messages", response_model=List[GameMessageDoc])
async def list_messages(game_id: str, limit: int = 50, offset: int = 0, db=Depends(get_db), current_user=Depends(get_current_user)):
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    cursor = _game_messages(db).find({"game_id": game_id}).sort("timestamp", 1).skip(offset).limit(limit)
    items: List[dict] = []
    async for it in cursor:
        it["_id"] = str(it.get("_id"))
        items.append(it)
    return items


@router.post("/{game_id}/actions", response_model=GameActionDoc)
async def propose_action(game_id: str, payload: dict | None = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    # Aceptar payload minimalista: { action: string, character_id?: string }
    action_text = (payload or {}).get("action", "").strip()
    if not action_text:
        raise HTTPException(status_code=422, detail="Campo 'action' es requerido")
    
    # Verificar que el juego existe y está en action_phase
    game = await _games(db).find_one({"_id": ObjectId(game_id)})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")
    
    game_state = game.get("game_state")
    if game_state == "closing":
        raise HTTPException(status_code=409, detail="No se pueden enviar acciones mientras se genera el capítulo. Espera a que termine.")
    elif game_state != "action_phase":
        raise HTTPException(status_code=409, detail=f"No se pueden enviar acciones en estado {game_state}. Espera a que se abra la fase de acciones.")
    
    # Determinar capítulo actual
    chap = int((payload or {}).get("chapter_number") or game.get("current_chapter", 1) or 1)
    doc = {
        "game_id": game_id,
        "user_id": str(current_user["_id"]),
        "character_id": (payload or {}).get("character_id"),
        "action": action_text,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "chapter_number": chap,
    }
    res = await _game_actions(db).insert_one(doc)
    created = await _game_actions(db).find_one({"_id": res.inserted_id})
    created["_id"] = str(created["_id"]) 
    
    # ✅ Auto-ready al proponer acción (mejora UX: acción enviada = listo)
    await _games(db).update_one(
        {"_id": ObjectId(game_id)},
        {"$addToSet": {"continue_ready": str(current_user["_id"])}}
    )

    # Emitir update para que la UI vea el conteo de listos
    members = [m async for m in _game_members(db).find({"game_id": game_id})]
    game_updated = await _games(db).find_one({"_id": ObjectId(game_id)})
    ready_list = [str(x) for x in (game_updated.get("continue_ready", []) or [])]

    await _broadcast_game(db, game_id, {
        "type": "game:continue_update",
        "data": {"ready_count": len(ready_list), "total": len(members), "remaining_seconds": 0}
    })
    
    # ✅ Re-evaluar condiciones de cierre tras proponer acción (igual que en mark_continue)
    total = len(members)
    ready_count = len(ready_list)

    # Calcular tiempo restante (manejo de borde <= 0)
    phase = game_updated.get("action_phase") or {}
    remaining_seconds = 0
    time_over = False
    ends_at_iso = phase.get("ends_at")
    if ends_at_iso:
        try:
            ends_at = datetime.fromisoformat(ends_at_iso)
            remaining_seconds = max(0, int((ends_at - datetime.utcnow()).total_seconds()))
            time_over = (remaining_seconds <= 0) or (datetime.utcnow() >= ends_at)
        except Exception:
            pass

    settings = game_updated.get("settings", {}) or {}
    require_all = settings.get("require_all_players", True)
    
    everyone_ready = require_all and total > 0 and ready_count == total
    reached_threshold = (not require_all) and ready_count >= max(1, int(total * 0.6))

    print(f"[propose_action] After action: ready_count={ready_count}/{total}, time_over={time_over}, everyone_ready={everyone_ready}, reached_threshold={reached_threshold}")

    # Si ya corresponde, cerrar fase y generar siguiente capítulo en background
    if everyone_ready or reached_threshold or time_over:
        print(f"[propose_action] Conditions met, enqueueing finalize for game {game_id}")
        
        # cancelar timer de la fase actual
        try:
            from .websockets import manager
            task = manager.action_phase_tasks.get(str(game_id))
            if task:
                task.cancel()
            manager.action_phase_tasks.pop(str(game_id), None)
        except Exception:
            pass

        # encolar finalize idempotente por capítulo
        current_chapter = int(game_updated.get("current_chapter", 0) or 0)
        asyncio.create_task(_finalize_actions_and_generate_next(db, ObjectId(game_id), expected_chapter=current_chapter))
    
    # Broadcast actions updated (optional)
    await _broadcast_game(db, game_id, {"type": "game:actions_updated", "data": {"chapter_number": chap}})
    return created


@router.get("/{game_id}/actions", response_model=List[GameActionDoc])
async def list_actions(game_id: str, status: str | None = None, db=Depends(get_db), current_user=Depends(get_current_user)):
    query = {"game_id": game_id}
    if status:
        query["status"] = status
    items: List[dict] = []
    async for it in _game_actions(db).find(query).sort("created_at", 1):
        it["_id"] = str(it.get("_id"))
        items.append(it)
    return items


@router.post("/{game_id}/chapters", response_model=GameChapterDoc)
async def add_chapter(game_id: str, payload: GameChapterDoc, db=Depends(get_db), current_user=Depends(get_current_user)):
    doc = payload.model_dump(by_alias=True)
    doc.update({
        "game_id": game_id,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": str(current_user["_id"]),
    })
    res = await _game_chapters(db).insert_one(doc)
    created = await _game_chapters(db).find_one({"_id": res.inserted_id})
    created["_id"] = str(created["_id"]) 
    # actualizar meta
    try:
        await _games(db).update_one({"_id": ObjectId(game_id)}, {"$inc": {"current_chapter": 1}})
    except Exception:
        pass
    return created


@router.get("/{game_id}/chapters", response_model=List[GameChapterDoc])
async def list_chapters(game_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    items: List[dict] = []
    async for it in _game_chapters(db).find({"game_id": game_id}).sort("chapter_number", 1):
        it["_id"] = str(it.get("_id"))
        items.append(it)
    return items


@router.patch("/{game_id}/settings")
async def update_settings(game_id: str, payload: dict, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Actualizar configuraciones del juego (solo admin)"""
    try:
        gid = ObjectId(game_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de ID inválido")
        
    game = await _games(db).find_one({"_id": gid})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")

    user_id = str(current_user["_id"])
    if user_id != game.get("admin_id"):
        raise HTTPException(status_code=403, detail="Solo el admin puede cambiar configuraciones")

    # Filtrar campos permitidos
    allowed = {"discussion_time", "auto_continue", "continue_time", "require_all_players", "allow_suggestions"}
    settings_updates = {k: payload[k] for k in allowed if k in payload}
    
    # max_chapters se actualiza en el campo raíz
    root_updates = {}
    if "max_chapters" in payload:
        # ✅ Validar que el número máximo de capítulos no exceda 20
        num_chapters = int(payload["max_chapters"])
        if num_chapters > 20:
            raise HTTPException(status_code=400, detail="El número máximo de capítulos no puede ser superior a 20")
        root_updates["max_chapters"] = num_chapters
    
    if not settings_updates and not root_updates:
        return {"ok": True, "message": "No hay cambios válidos"}

    update_doc = {}
    if settings_updates:
        update_doc.update({f"settings.{k}": v for k, v in settings_updates.items()})
    if root_updates:
        update_doc.update(root_updates)
    
    await _games(db).update_one({"_id": gid}, {"$set": update_doc})
    return {"ok": True, "message": "Configuraciones actualizadas"}


@router.get("/{game_id}/export.txt")
async def export_game_txt(game_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Exportar juego como archivo .txt"""
    try:
        gid = ObjectId(game_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de ID inválido")
        
    game = await _games(db).find_one({"_id": gid})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")

    # Traer capítulos ordenados
    chapters = [c async for c in _game_chapters(db).find({"game_id": game_id}).sort("chapter_number", 1)]
    
    # Construir texto
    parts = []
    title = (game.get("name") or f"Historia {game_id}").strip()
    parts.append(f"{title}\n\n")
    
    for ch in chapters:
        n = ch.get("chapter_number")
        parts.append(f"Capítulo {n}\n")
        parts.append("=" * 20 + "\n\n")
        parts.append((ch.get("content") or "").strip())
        parts.append("\n\n")
    
    content = "".join(parts)

    headers = {
        "Content-Disposition": f'attachment; filename="{title.replace(" ", "_")}.txt"'
    }
    return Response(content, media_type="text/plain; charset=utf-8", headers=headers)


@router.get("/{game_id}/export.pdf")
async def export_game_pdf(game_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    """Exportar juego como archivo .pdf"""
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        import textwrap
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF no disponible: falta dependencia reportlab")

    try:
        gid = ObjectId(game_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de ID inválido")
        
    game = await _games(db).find_one({"_id": gid})
    if not game:
        raise HTTPException(status_code=404, detail="Game no encontrado")

    chapters = [c async for c in _game_chapters(db).find({"game_id": game_id}).sort("chapter_number", 1)]
    title = (game.get("name") or f"Historia {game_id}").strip()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    # Portada simple
    c.setFont("Times-Bold", 18)
    c.drawString(1*inch, height-1.5*inch, title)
    c.setFont("Times-Roman", 12)
    c.drawString(1*inch, height-1.8*inch, f"Capítulos: {len(chapters)}")
    c.drawString(1*inch, height-2.1*inch, f"Generado: {datetime.utcnow().strftime('%Y-%m-%d')}")
    c.showPage()

    # Cuerpo
    for ch in chapters:
        text = c.beginText(1*inch, height-1*inch)
        text.setFont("Times-Bold", 14)
        text.textLine(f"Capítulo {ch.get('chapter_number')}")
        text.textLine("")
        text.setFont("Times-Roman", 11)
        
        # Wrap simple por líneas ~95 caracteres
        content = ch.get("content") or ""
        for line in content.splitlines():
            if line.strip():
                for wrapped in textwrap.wrap(line, width=95):
                    text.textLine(wrapped)
            else:
                text.textLine("")  # línea vacía
        
        c.drawText(text)
        c.showPage()

    c.save()
    pdf = buffer.getvalue()
    buffer.close()

    headers = {
        "Content-Disposition": f'attachment; filename="{title.replace(" ", "_")}.pdf"'
    }
    return Response(pdf, media_type="application/pdf", headers=headers)
