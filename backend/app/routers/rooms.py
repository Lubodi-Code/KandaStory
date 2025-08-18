from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from app.models.schemas import (
    RoomCreate, RoomPublic, ActionSuggestion, CharacterSelection, 
    ChatMessage, PlayerAction, RoomMessage
)
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.services.ai_service import generate_story_chapter, generate_story_chapter_async, AIService
from app.services.games_factory import create_game_from_room
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Helper para validar ObjectId
def _oid(room_id: str) -> ObjectId:
    """Convierte room_id a ObjectId con validación."""
    if not ObjectId.is_valid(room_id):
        raise HTTPException(status_code=400, detail="ID de sala inválido")
    return ObjectId(room_id)


def _rooms(db):
    return db["rooms"]


def _characters(db):
    return db["characters"]


def _users(db):
    return db["users"]


def _worlds(db):
    return db["worlds"]


# ---------- Utils ----------
def _to_serializable(obj):
    """Recursively convert Mongo ObjectIds and other non-serializable types to strings."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [_to_serializable(it) for it in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj

def _public_room_view(room: dict) -> dict:
    """Return a minimized, JSON-safe public representation of a room."""
    if not room:
        return {}
    safe = {
        "_id": str(room.get("_id") or ""),
        "id": str(room.get("_id") or ""),
        "name": room.get("name"),
        "world_id": str(room.get("world_id")) if room.get("world_id") else None,
        "max_players": room.get("max_players", 4),
        "game_state": room.get("game_state") or room.get("status") or "waiting",
        "created_at": room.get("created_at"),
        "current_members": len(room.get("member_ids", []) or []),
    }
    # Joinability flag for frontend UX
    try:
        state = safe.get("game_state", "waiting")
        current = int(safe.get("current_members", 0) or 0)
        capacity = int(safe.get("max_players", 4) or 4)
        safe["is_joinable"] = (state == "waiting" and current < capacity)
    except Exception:
        safe["is_joinable"] = False
    # Include world if present and already enriched by caller
    if room.get("world"):
        safe["world"] = _to_serializable(room["world"])  # ensure JSON-safe
    return safe


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    from app.core.security import decode_token
    try:
        payload = decode_token(token)
        uid = payload.get("sub")
        user = await _users(db).find_one({"_id": ObjectId(uid)})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Token invÃ¡lido")


@router.get("/rooms")
async def get_rooms(status: str = "open", db=Depends(get_db), user=Depends(get_current_user)):
    # Primero, eliminar salas con 0 miembros
    await _rooms(db).delete_many({"member_ids": {"$size": 0}})

    # âœ… Filtrar por status (por defecto solo salas abiertas)
    query = {"$or": [{"deleted": {"$exists": False}}, {"deleted": False}]}
    if status:
        query["status"] = status
    else:
        # Si no se especifica status, mostrar solo open (evitar closed/archived)
        query["$or"].append({"status": {"$exists": False}})  # para compatibilidad con salas antiguas
        query["status"] = {"$ne": "closed"}

    rooms = []
    async for room in _rooms(db).find(query):
        # IDs principales como string
        room["_id"] = str(room["_id"])
        room["id"] = room["_id"]

        # Convertir campos conocidos
        if "member_ids" in room and isinstance(room["member_ids"], list):
            room["member_ids"] = [str(mid) for mid in room["member_ids"]]
        if "admin_id" in room and room["admin_id"] is not None:
            room["admin_id"] = str(room["admin_id"])
        if "world_id" in room and room["world_id"] is not None:
            # Mantener como string si es vÃ¡lido, si no, dejar None
            wid_str = str(room["world_id"])
            room["world_id"] = wid_str if wid_str else None

        # Enriquecer info del mundo si el ID es vÃ¡lido
        wid = room.get("world_id")
        if wid and ObjectId.is_valid(str(wid)):
            world = await _worlds(db).find_one({"_id": ObjectId(str(wid))})
            if world:
                world["_id"] = str(world["_id"])
                world["id"] = world["_id"]
                room["world"] = world

        # MÃ©tricas y flags
        room["current_members"] = len(room.get("member_ids", []) or [])
        room["is_user_member"] = str(user["_id"]) in (room.get("member_ids", []) or [])
        try:
            state = room.get("game_state") or room.get("status") or "waiting"
            room["is_joinable"] = (state == "waiting" and int(room["current_members"]) < int(room.get("max_players", 4) or 4))
        except Exception:
            room["is_joinable"] = False

        # Serializar completamente para evitar ObjectId no serializable en anidados
        rooms.append(_to_serializable(room))
    
    return rooms


@router.get("/rooms/public")
async def get_public_rooms(db=Depends(get_db)):
    """Endpoint pÃºblico para listar salas disponibles (no requiere autenticaciÃ³n).
    Robusto ante world_id invÃ¡lidos o faltantes.
    """
    try:
        # Eliminar salas huÃ©rfanas (sin miembros)
        await _rooms(db).delete_many({"member_ids": {"$size": 0}})

        # Ocultar salas marcadas como eliminadas (convertidas a partidas)
        query = {"$or": [{"deleted": {"$exists": False}}, {"deleted": False}]}

        rooms = []
        async for room in _rooms(db).find(query):
            try:
                # IDs como string
                room["_id"] = str(room["_id"])
                room["id"] = room["_id"]

                # Incluir informaciÃ³n del mundo si es posible
                wid = room.get("world_id")
                world_oid = None
                if wid:
                    # Soportar tanto ObjectId como string; ignorar si invÃ¡lido
                    try:
                        wid_str = str(wid)
                        if ObjectId.is_valid(wid_str):
                            world_oid = ObjectId(wid_str)
                    except Exception:
                        world_oid = None

                if world_oid:
                    world = await _worlds(db).find_one({"_id": world_oid})
                    if world:
                        world["_id"] = str(world["_id"])
                        world["id"] = world["_id"]
                        room["world"] = world

                # Construir vista pÃºblica JSON-safe
                public_view = _public_room_view(room)
                rooms.append(public_view)
            except Exception as inner_e:
                # No abortar todo el listado por un registro defectuoso
                print(f"[rooms.public] Error procesando sala {room.get('_id')}: {inner_e}")
                continue

        return rooms
    except Exception as e:
        print(f"Error en get_public_rooms: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/rooms/{room_id}")
async def get_room_by_id(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    """Obtener sala por ID. Devuelve 410 Gone si la sala estÃ¡ cerrada."""
    try:
        room_oid = _oid(room_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de sala invÃ¡lido")
    
    room = await _rooms(db).find_one({"_id": room_oid})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    # âœ… Si la sala estÃ¡ cerrada, devolver 410 con game_id para redirecciÃ³n
    room_status = room.get("status", "open")
    if room_status != "open":
        game_id = room.get("game_id")
        if game_id:
            raise HTTPException(
                status_code=410, 
                detail={"message": "Sala cerrada", "redirect_game_id": str(game_id)}
            )
        else:
            raise HTTPException(status_code=410, detail={"message": "Sala cerrada"})
    
    # Normalizar y devolver sala abierta
    room["_id"] = str(room["_id"])
    room["id"] = room["_id"]
    
    # Convertir campos conocidos
    if "member_ids" in room and isinstance(room["member_ids"], list):
        room["member_ids"] = [str(mid) for mid in room["member_ids"]]
    if "admin_id" in room and room["admin_id"] is not None:
        room["admin_id"] = str(room["admin_id"])
    if "world_id" in room and room["world_id"] is not None:
        room["world_id"] = str(room["world_id"])
    
    # Cargar mundo si existe
    if room.get("world_id"):
        try:
            world = await _worlds(db).find_one({"_id": ObjectId(room["world_id"])})
            if world:
                world["_id"] = str(world["_id"])
                world["id"] = world["_id"]
                room["world"] = world
        except Exception:
            pass
    
    # MÃ©tricas y flags
    room["current_members"] = len(room.get("member_ids", []) or [])
    room["is_user_member"] = str(user["_id"]) in (room.get("member_ids", []) or [])
    try:
        current = len(room.get("member_ids", []) or [])
        capacity = int(room.get("max_players", 4) or 4)
        state = room.get("game_state") or room.get("status") or "waiting"
        room["is_joinable"] = (state == "waiting" and current < capacity)
    except Exception:
        room["is_joinable"] = False
    
    return _to_serializable(room)


    


@router.post("/rooms", response_model=RoomPublic)
async def create_room(data: RoomCreate, db=Depends(get_db), user=Depends(get_current_user)):
    # âœ… Verificar que el usuario no sea admin de otra sala ABIERTA
    existing_room = await _rooms(db).find_one({
        "admin_id": str(user["_id"]),
        "$or": [
            {"status": "open"},
            {"status": {"$exists": False}}  # para compatibilidad con salas sin status
        ]
    })
    if existing_room:
        raise HTTPException(status_code=400, detail="Ya tienes una sala abierta. Solo puedes administrar una sala abierta a la vez.")
    
    # Verificar que el mundo existe
    world = await _worlds(db).find_one({"_id": ObjectId(data.world_id)})
    if not world:
        raise HTTPException(status_code=404, detail="Mundo no encontrado")
    
    # ✅ Validar que el número máximo de capítulos no exceda 20
    if data.max_chapters > 20:
        raise HTTPException(status_code=400, detail="El número máximo de capítulos no puede ser superior a 20")
    
    # Incrementar contador de uso del mundo
    await _worlds(db).update_one(
        {"_id": ObjectId(data.world_id)},
        {"$inc": {"usage_count": 1}}
    )
    
    doc = data.model_dump()
    doc.update({
        "owner_id": str(user["_id"]),
        "admin_id": str(user["_id"]),  # El creador es el admin por defecto
        "member_ids": [str(user["_id"])],
        "members": [
            {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "is_ready": False,
            }
        ],
        "selected_characters": [],
        "current_chapter": 0,
        "chapters": [],
        "messages": [],
        "status": "open",  # âœ… Nueva sala siempre empieza abierta
        "game_state": "waiting",
        "ready_players": [],
        "suggestions": [],
        "created_at": datetime.utcnow().isoformat(),
    })
    
    res = await _rooms(db).insert_one(doc)
    created = await _rooms(db).find_one({"_id": res.inserted_id})
    created["_id"] = str(created["_id"])
    created["id"] = created["_id"]
    
    # Incluir informaciÃ³n del mundo
    world["_id"] = str(world["_id"])
    world["id"] = world["_id"]
    created["world"] = world
    
    return created


@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    member_ids = room.get("member_ids", [])
    max_players = room.get("max_players", 4)
    
    # Verificar si el usuario ya estÃ¡ en la sala
    if uid in member_ids:
        return {"joined": True, "message": "Ya estÃ¡s en esta sala"}
    # Bloquear unirse si la partida ya comenzÃ³ (solo para no-miembros)
    state = room.get("game_state") or room.get("status") or "waiting"
    if state != "waiting":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="GAME_ALREADY_STARTED")
    
    # Verificar si la sala estÃ¡ llena
    if len(member_ids) >= max_players:
        raise HTTPException(status_code=400, detail=f"La sala estÃ¡ llena. MÃ¡ximo {max_players} jugadores")
    
    # Actualizar tanto member_ids como members
    await _rooms(db).update_one(
        {"_id": _oid(room_id)}, 
        {
            "$addToSet": {
                "member_ids": uid,
                "members": {
                    "user_id": uid,
                    "username": user["username"],
                    "is_ready": False
                }
            }
        }
    )
    return {"joined": True, "message": "Te has unido a la sala exitosamente"}


@router.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    """Salir de una sala"""
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    member_ids = room.get("member_ids", [])
    
    # Verificar si el usuario estÃ¡ en la sala
    if uid not in member_ids:
        raise HTTPException(status_code=400, detail="No estÃ¡s en esta sala")
    
    # Remover al usuario de la sala
    member_ids.remove(uid)
    
    # Si no quedan miembros, eliminar la sala
    if len(member_ids) == 0:
        await _rooms(db).delete_one({"_id": _oid(room_id)})
        return {"left": True, "message": "Has salido de la sala. La sala ha sido eliminada por estar vacÃ­a."}
    
    # Si el usuario que se va es el admin y hay otros miembros, transferir admin
    if room.get("admin_id") == uid:
        new_admin_id = member_ids[0]  # El primer miembro restante se convierte en admin
        await _rooms(db).update_one(
            {"_id": _oid(room_id)}, 
            {
                "$set": {"member_ids": member_ids, "admin_id": new_admin_id},
                "$pull": {
                    "ready_players": uid,
                    "members": {"user_id": uid}
                }
            }
        )
        return {"left": True, "message": f"Has salido de la sala. El admin ha sido transferido."}
    else:
        # Usuario normal saliendo
        await _rooms(db).update_one(
            {"_id": _oid(room_id)}, 
            {
                "$set": {"member_ids": member_ids},
                "$pull": {
                    "ready_players": uid,
                    "members": {"user_id": uid}
                }
            }
        )
        return {"left": True, "message": "Has salido de la sala exitosamente"}


@router.post("/rooms/{room_id}/chapter")
async def generate_chapter(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    # Only admin can generate next chapter
    if str(user["_id"]) != room.get("admin_id"):
        raise HTTPException(status_code=403, detail="Solo el admin puede generar capÃ­tulos")

    # Pull characters of room members
    member_ids = room.get("member_ids", [])
    chars = []
    async for ch in _characters(db).find({"owner_id": {"$in": member_ids}}):
        ch["_id"] = str(ch["_id"]) 
        chars.append(ch)

    text = generate_story_chapter(room, chars, room.get("suggestions", []))

    await _rooms(db).update_one({"_id": _oid(room_id)}, {"$push": {"chapters": text}, "$set": {"suggestions": []}})
    return {"chapter": text}


@router.post("/rooms/{room_id}/suggest")
async def suggest_action(room_id: str, suggestion: ActionSuggestion, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    # Verificar si las sugerencias estÃ¡n permitidas en esta sala
    if not room.get("allow_suggestions", True):
        raise HTTPException(status_code=403, detail="Las sugerencias no estÃ¡n permitidas en esta sala")
    
    # Verificar que el usuario sea miembro de la sala
    uid = str(user["_id"])
    if uid not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="Debes ser miembro de la sala para hacer sugerencias")

    await _rooms(db).update_one({"_id": _oid(room_id)}, {"$push": {"suggestions": suggestion.text}})
    return {"accepted": True, "message": "Sugerencia aÃ±adida exitosamente"}


    


@router.post("/rooms/{room_id}/select-character")
async def select_character(room_id: str, selection: CharacterSelection, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    if uid not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="No eres miembro de esta sala")
    
    # Verificar que el personaje existe y pertenece al usuario
    character = await _characters(db).find_one({
        "_id": ObjectId(selection.character_id),
        "owner_id": uid
    })
    if not character:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    # Remover selecciÃ³n anterior del usuario si existe
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$pull": {"selected_characters": {"user_id": uid}}}
    )
    
    # AÃ±adir nueva selecciÃ³n
    character_data = {
        "user_id": uid,
        "character_id": str(character["_id"]),
        "character_name": character["name"],
        "character": character
    }
    
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$push": {"selected_characters": character_data}}
    )
    
    # Obtener la sala actualizada para enviar por WebSocket
    updated_room = await _rooms(db).find_one({"_id": _oid(room_id)})
    
    # Convertir ObjectId a string en selected_characters para que sea JSON serializable
    selected_characters = []
    for sc in updated_room.get("selected_characters", []):
        # Crear una copia del personaje con ObjectId convertidos a string
        character_copy = dict(sc.get("character", {}))
        if "_id" in character_copy:
            character_copy["_id"] = str(character_copy["_id"])
        if "owner_id" in character_copy:
            character_copy["owner_id"] = str(character_copy["owner_id"])
        
        selected_char = {
            "user_id": sc["user_id"],
            "character_id": sc["character_id"],
            "character_name": sc["character_name"],
            "character": character_copy
        }
        selected_characters.append(selected_char)
    
    # Notificar a todos los miembros de la sala por WebSocket
    from .websockets import notify_room_members
    await notify_room_members(room_id, {
        "type": "character_selected",
        "data": {
            "selected_characters": selected_characters,
            "user_id": uid,
            "character_name": character["name"]
        }
    })
    
    return {"message": "Personaje seleccionado correctamente"}


@router.get("/my-room")
async def get_my_room(db=Depends(get_db), user=Depends(get_current_user)):
    """Obtener la sala del usuario actual"""
    try:
        uid = str(user["_id"])
        
        # Buscar sala donde el usuario es miembro y que esté activa
        room = await _rooms(db).find_one({
            "member_ids": uid,
            "game_state": {"$in": ["waiting", "character_selection"]}  # Solo salas activas
        })
        
        if not room:
            return {"room": None, "message": "No tienes salas activas"}
        
        # Convertir ObjectId a string
        room["_id"] = str(room["_id"])
        room["id"] = room["_id"]
        
        # Obtener información de los miembros
        members = []
        for member_id in room.get("member_ids", []):
            try:
                member = await _users(db).find_one({"_id": ObjectId(member_id)})
                if member:
                    members.append({
                        "user_id": member_id,
                        "username": member["username"],
                        "is_ready": member_id in room.get("ready_players", [])
                    })
            except Exception as e:
                print(f"Error getting member {member_id}: {e}")
                continue
        
        room["members"] = members
        
        # Obtener información del mundo si existe
        if room.get("world_id"):
            try:
                world = await _worlds(db).find_one({"_id": ObjectId(room["world_id"])})
                if world:
                    world["_id"] = str(world["_id"])
                    world["id"] = world["_id"]
                    room["world"] = world
            except Exception as e:
                print(f"Error getting world: {e}")
                pass
        
        return {"room": room}
    except Exception as e:
        print(f"Error in get_my_room: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.post("/rooms/{room_id}/ready")
async def toggle_ready(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    if uid not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="No eres miembro de esta sala")
    
    ready_players = room.get("ready_players", [])
    
    if uid in ready_players:
        # Quitar de listos
        await _rooms(db).update_one(
            {"_id": _oid(room_id)},
            {"$pull": {"ready_players": uid}}
        )
        is_ready = False
    else:
        # AÃ±adir a listos
        await _rooms(db).update_one(
            {"_id": _oid(room_id)},
            {"$addToSet": {"ready_players": uid}}
        )
        is_ready = True
    
    # Verificar si todos estÃ¡n listos para comenzar el juego
    updated_room = await _rooms(db).find_one({"_id": _oid(room_id)})
    ready_count = len(updated_room.get("ready_players", []))
    total_members = len(updated_room.get("member_ids", []))
    
    if ready_count == total_members and ready_count > 0:
        # Todos estÃ¡n listos, comenzar el juego
        await _rooms(db).update_one(
            {"_id": _oid(room_id)},
            {"$set": {"game_state": "playing"}}
        )
        
        # Generar primer capÃ­tulo
        await generate_first_chapter(room_id, db)
    
    return {"is_ready": is_ready, "ready_count": ready_count, "total_members": total_members}


@router.post("/rooms/{room_id}/message")
async def send_message(room_id: str, message: ChatMessage, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    if uid not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="No eres miembro de esta sala")
    
    room_message = {
        "user_id": uid,
        "username": user["username"],
        "message": message.message,
        "message_type": message.message_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$push": {"messages": room_message}}
    )
    
    return {"message": "Mensaje enviado"}


@router.post("/rooms/{room_id}/action")
async def submit_action(room_id: str, action: PlayerAction, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    if uid not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="No eres miembro de esta sala")
    
    if room.get("game_state") != "discussion":
        raise HTTPException(status_code=400, detail="No es momento para enviar acciones")
    
    # Remover acciÃ³n anterior del usuario si existe
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$pull": {"current_actions": {"user_id": uid}}}
    )
    
    # AÃ±adir nueva acciÃ³n
    action_data = {
        "user_id": uid,
        "username": user["username"],
        "action": action.action,
        "character_id": action.character_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$push": {"current_actions": action_data}}
    )
    
    return {"message": "AcciÃ³n enviada"}


async def generate_first_chapter(room_id: str, db):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    characters = room.get("selected_characters", [])
    
    if not characters:
        return
    
    # Generar primer capÃ­tulo
    chapter_text = generate_story_chapter(room, [char["character"] for char in characters], [])
    
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {
            "$push": {"chapters": chapter_text},
            "$set": {
                "current_chapter": 1,
                "game_state": "discussion"
            },
            "$unset": {"ready_players": ""}
        }
    )


@router.post("/rooms/{room_id}/start-game")
async def start_game(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    # Solo el admin puede iniciar el juego
    if str(user["_id"]) != room.get("admin_id"):
        raise HTTPException(status_code=403, detail="Solo el admin puede iniciar el juego")

    # âœ… Idempotencia: si ya existe un game para esta room, retornar ese
    existing_game_id = room.get("game_id")
    if existing_game_id:
        return {"message": "Juego ya iniciado", "game_id": existing_game_id}

    # Verificar que todos los jugadores estÃ©n listos y tengan personajes
    member_ids = room.get("member_ids", [])
    ready_players = room.get("ready_players", [])
    selected_characters = room.get("selected_characters", [])

    if len(ready_players) != len(member_ids):
        raise HTTPException(status_code=400, detail="No todos los jugadores estÃ¡n listos")

    if len(selected_characters) != len(member_ids):
        raise HTTPException(status_code=400, detail="No todos los jugadores han seleccionado un personaje")

    # Crear juego real y persistir capÃ­tulo 1 (misma lÃ³gica que WS)
    try:
        game_id_value = await create_game_from_room(db, room_id)
    except Exception:
        game_id_value = None

    if not game_id_value:
        raise HTTPException(status_code=500, detail="Error creando el juego")

    # Generar primer capÃ­tulo con IA y persistir en game_chapters
    try:
        ai = AIService()
        world = None
        if room.get("world_id"):
            try:
                world = await db["worlds"].find_one({"_id": ObjectId(room["world_id"])})
            except Exception:
                world = None
        first = await ai.generate_first_chapter(world=world or {}, characters=room.get("selected_characters", []))
        
        await db["game_chapters"].insert_one({
            "game_id": str(game_id_value),
            "chapter_number": 1,
            "content": first,
            "created_at": datetime.utcnow().isoformat(),
        })
        
        # actualizar meta en games
        await db["games"].update_one({"_id": ObjectId(game_id_value)}, {"$set": {"current_chapter": 1}})
        
        # âœ… CERRAR LA SALA: marcar como closed y enlazar game_id
        await _rooms(db).update_one({"_id": _oid(room_id)}, {"$set": {
            "status": "closed",
            "game_id": str(game_id_value),
            "closed_at": datetime.utcnow().isoformat(),
            "game_state": "playing",
            "current_chapter": 1,
            "chapters": [first],
        }})
        
        # âœ… Broadcast simultÃ¡neo (WS) a todos en la sala
        from .websockets import notify_room_members
        await notify_room_members(room_id, {"type": "game_started", "data": {"game_id": str(game_id_value)}})
        await notify_room_members(room_id, {"type": "room_closed", "data": {"room_id": room_id}})
        await notify_room_members(room_id, {"type": "chapter_update", "data": {"chapter_number": 1, "text": first, "actions_used": []}})
        
        return {"message": "Juego iniciado exitosamente", "game_id": str(game_id_value)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando juego: {e}")


@router.post("/rooms/{room_id}/action")
async def submit_action(room_id: str, action_data: dict, db=Depends(get_db), user=Depends(get_current_user)):
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    uid = str(user["_id"])
    if uid not in room.get("member_ids", []):
        raise HTTPException(status_code=403, detail="No eres miembro de esta sala")

    # Verificar que el juego estÃ© en estado de juego
    if room.get("game_state") != "playing":
        raise HTTPException(status_code=400, detail="El juego no estÃ¡ en estado de juego")

    # Verificar que las acciones estÃ©n permitidas
    if not room.get("allow_actions", False):
        raise HTTPException(status_code=400, detail="Las acciones no estÃ¡n permitidas en esta sala")

    # Obtener informaciÃ³n del personaje del usuario
    user_character = None
    for sc in room.get("selected_characters", []):
        if sc["user_id"] == uid:
            user_character = sc
            break
    
    if not user_character:
        raise HTTPException(status_code=400, detail="No tienes un personaje seleccionado")

    # Crear la acciÃ³n
    action = {
        "id": str(ObjectId()),
        "user_id": uid,
        "character_id": user_character["character_id"],
        "character_name": user_character["character_name"],
        "action": action_data.get("action", ""),
        "timestamp": datetime.utcnow().isoformat()
    }

    # Agregar acciÃ³n a las pendientes (reemplazar si ya existe una del usuario)
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$pull": {"pending_actions": {"user_id": uid}}}
    )
    
    await _rooms(db).update_one(
        {"_id": _oid(room_id)},
        {"$push": {"pending_actions": action}}
    )

    return {"message": "AcciÃ³n enviada correctamente"}


@router.patch("/rooms/{room_id}")
async def update_room(room_id: str, payload: dict, db=Depends(get_db), user=Depends(get_current_user)):
    """Actualizar ajustes de la sala (solo admin). Soporta max_chapters con tope 20."""
    room = await _rooms(db).find_one({"_id": _oid(room_id)})
    if not room:
        raise HTTPException(status_code=404, detail="Sala no encontrada")

    if str(user["_id"]) != room.get("admin_id"):
        raise HTTPException(status_code=403, detail="Solo el admin puede actualizar la sala")

    update_doc = {}
    # Permitir actualizar max_chapters con validación
    if "max_chapters" in payload:
        try:
            num = int(payload["max_chapters"])
        except Exception:
            raise HTTPException(status_code=400, detail="max_chapters debe ser un número entero")
        if num < 1 or num > 20:
            raise HTTPException(status_code=400, detail="El número máximo de capítulos debe estar entre 1 y 20")
        update_doc["max_chapters"] = num

    # Otros campos permitidos (ejemplo: discussion_time, auto_continue)
    allowed = {"discussion_time", "auto_continue", "continue_time", "max_players", "allow_suggestions"}
    for k in allowed:
        if k in payload:
            update_doc[k] = payload[k]

    if not update_doc:
        return {"ok": True, "message": "No hay cambios válidos"}

    await _rooms(db).update_one({"_id": _oid(room_id)}, {"$set": update_doc})
    return {"ok": True, "message": "Sala actualizada", "updated": update_doc}


@router.post("/rooms/{room_id}/hard-delete")
async def hard_delete_room(room_id: str, db=Depends(get_db), user=Depends(get_current_user)):
    """Eliminar sala definitivamente después de que el juego haya iniciado.
    Idempotente: si ya se borró, devuelve 200."""
    try:
        room_oid = _oid(room_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de sala inválido")
    
    # Verificar permisos: admin/owner o miembro de la sala relacionada al juego
    room = await _rooms(db).find_one({"_id": room_oid}, {"admin_id": 1, "member_ids": 1, "game_id": 1})
    if room:
        uid = str(user["_id"])
        is_admin = str(room.get("admin_id")) == uid
        is_member = uid in (room.get("member_ids", []) or [])
        if not (is_admin or is_member):
            raise HTTPException(status_code=403, detail="No tienes permisos para eliminar esta sala")
    
    # Idempotente: si ya no existe, devolver ok
    res = await _rooms(db).delete_one({"_id": room_oid})
    
    # Broadcast opcional por si queda alguien conectado en WS de sala
    try:
        from .websockets import manager
        await manager.broadcast_to_room({"type": "room_deleted", "data": {"room_id": room_id}}, f"room:{room_id}")
        # Cerrar conexiones WebSocket de la sala si existen
        if hasattr(manager, 'close_room_connections'):
            await manager.close_room_connections(room_id)
    except Exception:
        pass
    
    return {"deleted": True, "was_found": res.deleted_count > 0}

