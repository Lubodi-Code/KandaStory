from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List, Set, Optional
import json
import asyncio
from urllib.parse import urlparse, parse_qsl
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import decode_token
from bson import ObjectId
from app.services.ai_service import AIService
from app.services.games_factory import create_game_from_room, DEFAULT_CONTINUE_TIME

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class ConnectionManager:
    def __init__(self):
        # Diccionario: room_id -> Set de WebSockets
        self.active_connections = {}
        # Diccionario: WebSocket -> user_id
        self.user_connections = {}
        # Tareas por sala para fase de acciones
        self.action_phase_tasks = {}
        # Tareas por sala para modo auto (sin acciones)
        self.auto_mode_tasks = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        self.user_connections[websocket] = user_id

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        if websocket in self.user_connections:
            del self.user_connections[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass

    async def broadcast_to_room(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            # Asegurar serialización robusta
            try:
                message_text = json.dumps(message)
            except Exception:
                try:
                    message_text = json.dumps(_to_serializable(message))
                except Exception as e:
                    print(f"[websocket.broadcast] Failed to serialize message: {e}")
                    return

            disconnected = []
            for connection in self.active_connections[room_id].copy():
                try:
                    await connection.send_text(message_text)
                except Exception:
                    disconnected.append(connection)
            # Remover conexiones desconectadas
            for connection in disconnected:
                self.disconnect(connection, room_id)

    async def schedule_action_phase_timer(self, game_id: str, ends_at_iso: str, db):
        """Iniciar timer para la fase de acciones de un juego"""
        # Cancelar timer existente si lo hay
        if game_id in self.action_phase_tasks:
            try:
                self.action_phase_tasks[game_id].cancel()
            except Exception:
                pass
        
        task = asyncio.create_task(self._run_action_phase_timer(game_id, ends_at_iso, db))
        self.action_phase_tasks[game_id] = task

    async def _run_action_phase_timer(self, game_id: str, ends_at_iso: str, db):
        """Loop del timer para enviar updates periódicos durante la fase de acciones"""
        try:
            from datetime import datetime
            ends_at = datetime.fromisoformat(ends_at_iso.replace('Z', '+00:00'))
            
            while True:
                now = datetime.utcnow()
                remaining = max(0, int((ends_at - now).total_seconds()))
                
                # Obtener estado actual del juego
                game = await _games(db).find_one({"_id": ObjectId(game_id)})
                if not game or game.get("game_state") != "action_phase":
                    break
                
                # Obtener miembros y ready list
                members = [m async for m in _game_members(db).find({"game_id": game_id})]
                total = len(members)
                ready_list = [str(x) for x in (game.get("continue_ready", []) or [])]
                
                # Enviar update
                await self.broadcast_to_room({
                    "type": "game:continue_update",
                    "data": {
                        "ready_count": len(ready_list),
                        "total": total,
                        "remaining_seconds": remaining,
                    }
                }, f"game:{game_id}")
                
                # Si el tiempo se acabó o todos están listos, continuar
                if remaining <= 0 or (total > 0 and len(ready_list) >= total):
                    await self._auto_continue_game(game_id, db)
                    break
                
                # Esperar 3 segundos antes del próximo update
                await asyncio.sleep(3)
                
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[_run_action_phase_timer] error: {e}")

    async def _auto_continue_game(self, game_id: str, db):
        """Continuar automáticamente el juego delegando a la función centralizada de games.py"""
        try:
            print(f"[_auto_continue_game] Delegating to centralized finalize function for game {game_id}")
            # Delegar a la función centralizada en games.py (importar dinámicamente para evitar circular imports)
            from .games import _finalize_actions_and_generate_next
            from bson import ObjectId
            await _finalize_actions_and_generate_next(db, ObjectId(game_id))
        except Exception as e:
            print(f"[_auto_continue_game] error: {e}")

manager = ConnectionManager()

def _rooms(db):
    return db["rooms"]

def _users(db):
    return db["users"]

def _games(db):
    return db["games"]

def _game_members(db):
    return db["game_members"]

async def get_current_user_ws(token: str, db):
    """Obtener usuario actual para WebSocket"""
    try:
        payload = decode_token(token)
        uid = payload.get("sub")
        user = await _users(db).find_one({"_id": ObjectId(uid)})
        if not user:
            return None
        return user
    except Exception:
        return None

# Utilidad para convertir ObjectId y tipos no serializables a string
def _to_serializable(obj):
    try:
        from bson import ObjectId as _OID
    except Exception:
        _OID = None
    if _OID and isinstance(obj, _OID):
        return str(obj)
    if isinstance(obj, list):
        return [_to_serializable(it) for it in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj

@router.websocket("/ws/{room_id}")
@router.websocket("/ws/room/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: Optional[str] = None, access_token: Optional[str] = None, db=Depends(get_db)):
    # Aceptar token o access_token desde la query
    token = token or access_token
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    # Verificar autenticación
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    user_id = str(user["_id"])
    
    # Verificar que la sala existe
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        await websocket.close(code=1008, reason="Room not found")
        return
    
    # Verificar que el usuario es miembro de la sala
    if user_id not in room.get("member_ids", []):
        await websocket.close(code=1008, reason="Not a member of this room")
        return
    
    await manager.connect(websocket, room_id, user_id)
    print(f"[websocket] 🔗 Conexión establecida: usuario={user['username']} (id={user_id}) sala={room_id}")
    
    try:
        # Notificar a todos los usuarios (incluido el nuevo) con el estado actualizado de la sala
        updated_room_data = await get_room_data(room_id, db)
        if updated_room_data:
            await manager.broadcast_to_room({
                "type": "room_update",
                "data": updated_room_data
            }, room_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_websocket_message(message, room_id, user_id, user["username"], db)
                
        except WebSocketDisconnect:
            pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, room_id)
        print(f"[websocket] ❌ Desconexión: usuario_id={user_id} sala={room_id}")
        # No alteramos ready_players ni selected_characters en desconexión automática.

        # Notificar a otros usuarios que se desconectó y enviar estado actualizado
        # Comprobar si la sala todavía existe y tiene miembros
        remaining_room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
        if remaining_room and remaining_room.get("member_ids"):
            updated_room_data = await get_room_data(room_id, db)
            if updated_room_data:
                await manager.broadcast_to_room({
                    "type": "room_update",
                    "data": updated_room_data
                }, room_id)
        else:
            # Opcional: si no quedan miembros, se podría borrar la sala
            if remaining_room:
                await _rooms(db).delete_one({"_id": ObjectId(room_id)})
                print(f"Room {room_id} deleted as it is now empty.")
            else:
                print(f"Room {room_id} was already deleted or not found.")

async def handle_websocket_message(message: dict, room_id: str, user_id: str, username: str, db):
    """Manejar mensajes WebSocket"""
    message_type = message.get("type")
    
    if message_type == "chat_message":
        await handle_chat_message(message, room_id, user_id, username, db)
    elif message_type == "toggle_ready":
        await handle_toggle_ready(room_id, user_id, db)
    elif message_type == "select_character":
        await handle_select_character(message, room_id, user_id, db)
    elif message_type == "start_action_phase":
        await handle_start_action_phase(message, room_id, user_id, db)
    elif message_type == "submit_action":
        await handle_submit_action(message, room_id, user_id, username, db)
    elif message_type == "accept_suggestion":
        # Alias de submit_action con flag
        await handle_submit_action(message, room_id, user_id, username, db, accepted_from_ai=True)
    elif message_type == "mark_ready":
        await handle_mark_ready(room_id, user_id, db)
    elif message_type == "continue_ready":
        await handle_continue_ready(room_id, user_id, db)

async def handle_continue_ready(room_id: str, user_id: str, db):
    """Jugador marca listo para continuar (en contexto de juego). Delega a la función centralizada."""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        return
    game_id = room.get("game_id")
    if not game_id:
        return
    
    # Marcar listo en games
    await db["games"].update_one({"_id": ObjectId(game_id)}, {"$addToSet": {"continue_ready": user_id}})
    game = await db["games"].find_one({"_id": ObjectId(game_id)})
    
    # Calcular umbral (consenso total)
    members = [m async for m in db["game_members"].find({"game_id": str(game_id)})]
    total = len(members)
    ready = [str(x) for x in (game.get("continue_ready", []) or [])]
    
    # Emit update
    await manager.broadcast_to_room({
        "type": "game:continue_update",
        "data": {"ready_count": len(ready), "total": total}
    }, f"game:{game_id}")
    
    # Si todos están listos, delegar al cierre centralizado
    if total > 0 and len(ready) >= total:
        try:
            # Importar y usar la función centralizada de games.py
            from .games import _finalize_actions_and_generate_next
            import asyncio
            asyncio.create_task(_finalize_actions_and_generate_next(db, ObjectId(game_id)))
        except Exception as e:
            print(f"Error delegating to centralized finalize: {e}")

async def handle_chat_message(message: dict, room_id: str, user_id: str, username: str, db):
    """Manejar mensaje de chat"""
    from datetime import datetime
    
    chat_message = {
        "user_id": user_id,
        "username": username,
        "message": message.get("message", ""),
        "message_type": message.get("message_type", "chat"),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Guardar en base de datos
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$push": {"messages": chat_message}}
    )
    
    # Broadcast a todos los usuarios
    await manager.broadcast_to_room({
        "type": "new_message",
        "data": chat_message
    }, room_id)

async def handle_toggle_ready(room_id: str, user_id: str, db):
    """Manejar cambio de estado listo. Si todos están listos, el admin inicia el juego."""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        return

    # Actualizar lista de jugadores listos
    ready_players = set(room.get("ready_players", []))
    if user_id in ready_players:
        ready_players.remove(user_id)
        is_ready = False
    else:
        ready_players.add(user_id)
        is_ready = True

    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)}, {"$set": {"ready_players": list(ready_players)}}
    )

    # Refrescar datos de la sala
    updated_room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    member_ids = updated_room.get("member_ids", []) or []
    current_ready_players = updated_room.get("ready_players", [])

    # Notificar a todos los clientes en la sala sobre el cambio de estado
    await manager.broadcast_to_room({
        "type": "ready_update",
        "data": {
            "ready_count": len(current_ready_players),
            "total_members": len(member_ids),
            "ready_players": current_ready_players,
            "user_ready": user_id in current_ready_players
        }
    }, room_id)

    all_ready = len(member_ids) > 0 and len(current_ready_players) == len(member_ids)

    # Si todos están listos y quien pulsó 'listo' es el admin, se inicia el juego.
    if all_ready and user_id == str(room.get("admin_id")):
        try:
            # Usar la función centralizada completa que incluye generación de primer capítulo
            from .games import _create_complete_game_from_room
            game_id = await _create_complete_game_from_room(db, room_id)

            # Notificar a todos los jugadores que el juego ha comenzado (evento estándar en canal de sala)
            await manager.broadcast_to_room({
                "type": "room:started",
                "data": {"game_id": game_id}
            }, room_id)

            # Eliminar la sala porque ya no se usa
            await _rooms(db).delete_one({"_id": ObjectId(room_id)})
            print(f"Room {room_id} deleted after starting game {game_id} with first chapter.")

        except Exception as e:
            print(f"[websocket.toggle_ready] Error starting game: {e}")
            # Revertir el estado de listo si falla la creación del juego
            await _rooms(db).update_one(
                {"_id": ObjectId(room_id)},
                {"$pull": {"ready_players": user_id}}
            )
    else:
        # Si no, solo notificar el cambio de estado de "listo"
        await manager.broadcast_to_room({
            "type": "ready_update",
            "data": {
                "user_id": user_id,
                "is_ready": is_ready,
                "ready_players": current_ready_players
            }
        }, room_id)

async def handle_select_character(message: dict, room_id: str, user_id: str, db):
    """Manejar selección de personaje"""
    character_id = message.get("character_id")
    if not character_id:
        return
    
    # Obtener datos del personaje
    characters_collection = db["characters"]
    character = await characters_collection.find_one({"_id": ObjectId(character_id)})
    if not character:
        return
    
    # Verificar que el personaje pertenece al usuario
    if str(character.get("owner_id")) != str(user_id):
        return
    
    # Remover selección anterior del usuario
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$pull": {"selected_characters": {"user_id": user_id}}}
    )
    
    # Añadir nueva selección
    character_selection = {
        "user_id": user_id,
        "character_id": character_id,
        "character_name": character["name"],
        "character": character
    }
    
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$push": {"selected_characters": character_selection}}
    )
    
    # Broadcast a todos los usuarios
    await manager.broadcast_to_room({
        "type": "character_selected",
        "data": character_selection
    }, room_id)


@router.websocket("/ws/game/{game_id}")
async def websocket_game_endpoint(websocket: WebSocket, game_id: str, db=Depends(get_db)):
    """WebSocket para canal de juego (game:{game_id})."""
    # Extraer token de la query string
    query = dict(parse_qsl(urlparse(str(websocket.url)).query))
    token = query.get("token") or query.get("access_token")
    
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    user_id = str(user["_id"])
    gid = str(game_id)
    
    # 1) intenta como strings
    m = await _game_members(db).find_one({"game_id": gid, "user_id": user_id})
    
    # 2) si no, intenta con ObjectId (por si los guardaste así)
    if not m:
        try:
            m = await _game_members(db).find_one({
                "game_id": gid,
                "user_id": ObjectId(user_id)
            })
        except Exception:
            m = None
    
    # 3) último recurso: valida desde rooms.link y auto-repara membresía
    if not m:
        room = await _rooms(db).find_one({"game_id": gid, "member_ids": user_id})
        if not room and ObjectId.is_valid(user_id):
            room = await _rooms(db).find_one({"game_id": gid, "member_ids": str(user_id)})
        if room:
            await _game_members(db).insert_one({
                "game_id": gid, 
                "user_id": user_id, 
                "joined_at": datetime.utcnow().isoformat()
            })
        else:
            await websocket.close(code=1008)  # policy violation (no miembro)
            return

    channel_key = f"game:{game_id}"
    await manager.connect(websocket, channel_key, user_id)
    
    # Enviar estado actual de la fase de acciones si está activa
    try:
        game = await _games(db).find_one({"_id": ObjectId(game_id)})
        if game and game.get("game_state") == "action_phase" and game.get("action_phase"):
            action_phase = game["action_phase"]
            await manager.send_personal_message(json.dumps({
                "type": "game:action_phase_started",
                "data": {
                    "ends_at": action_phase.get("ends_at"),
                    "seconds_total": action_phase.get("seconds_total", 60),
                    "auto_continue": bool(game.get("settings", {}).get("auto_continue", True))
                }
            }), websocket)
    except Exception as e:
        print(f"Error sending action phase state: {e}")
    
    try:
        # Por ahora, solo mantener conexión y permitir broadcasts
        while True:
            # Mantener viva la conexión; clientes no envían mensajes por este canal todavía
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ws.game] error: {e}")
    finally:
        manager.disconnect(websocket, channel_key)

async def get_room_data(room_id: str, db):
    """Obtener datos completos de la sala"""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        return None
    # Normalizar IDs a string
    member_ids = [str(uid) for uid in (room.get("member_ids", []) or [])]
    ready_players = [str(uid) for uid in (room.get("ready_players", []) or [])]

    # Obtener información de los miembros
    members = []
    for uid in member_ids:
        try:
            user = await _users(db).find_one({"_id": ObjectId(uid)})
            if user:
                members.append({
                    "user_id": uid,
                    "username": user.get("username", ""),
                    "is_ready": uid in ready_players
                })
        except Exception as e:
            print(f"[ws.get_room_data] member load error {uid}: {e}")
            continue

    # Limpiar selected_characters para que sean JSON-safe
    cleaned_selected = []
    for sc in (room.get("selected_characters", []) or []):
        try:
            sc_copy = dict(sc)
            # Si es formato legacy con 'character' anidado, convertir IDs
            if isinstance(sc_copy.get("character"), dict):
                ch = dict(sc_copy["character"])
                if "_id" in ch:
                    ch["_id"] = str(ch["_id"])
                if "owner_id" in ch:
                    ch["owner_id"] = str(ch["owner_id"])
                sc_copy["character"] = _to_serializable(ch)
            # Forzar a string campos comunes
            for key in ("user_id", "character_id"):
                if key in sc_copy and sc_copy[key] is not None:
                    sc_copy[key] = str(sc_copy[key])
            cleaned_selected.append(_to_serializable(sc_copy))
        except Exception as e:
            print(f"[ws.get_room_data] selected_characters cleanup error: {e}")
            continue

    room_data = {
        "id": str(room.get("_id")),
        "name": room.get("name", ""),
        "game_state": room.get("game_state", "waiting"),
    "game_id": str(room.get("game_id")) if room.get("game_id") else None,
        "members": members,
        "member_ids": member_ids,
        "selected_characters": cleaned_selected,
        "messages": _to_serializable(room.get("messages", [])),
        "ready_players": ready_players,
        "max_players": int(room.get("max_players", 4) or 4),
        "admin_id": str(room.get("admin_id", "")),
        "chapters": [str(c) for c in (room.get("chapters", []) or [])],
        "current_chapter": int(room.get("current_chapter", 0) or 0),
    "discussion_time": int(room.get("discussion_time", 300) or 300),
    "auto_continue": bool(room.get("auto_continue", False)),
    "continue_time": int(room.get("continue_time", 60) or 60),
    "allow_actions": bool(room.get("allow_actions", True)),
    "action_time_minutes": int(room.get("action_time_minutes", 5) or 5),
    "pending_actions": _to_serializable(room.get("pending_actions", [])),
    "action_ready_players": [str(uid) for uid in (room.get("action_ready_players", []) or [])],
        "action_phase_deadline": room.get("action_phase_deadline") or None
    }

    # Tiempo restante si hay fase de acciones activa
    if room_data.get("game_state") == "action_phase":
        room_data["time_remaining"] = _compute_time_remaining(room)

    return room_data


# Función helper para notificar a los miembros de una sala
async def notify_room_members(room_id: str, message: dict):
    """Envía un mensaje a todos los miembros conectados de una sala"""
    await manager.broadcast_to_room(message, room_id)


# ========== Gestión de fase de acciones ==========
async def handle_start_action_phase(message: dict, room_id: str, user_id: str, db):
    """Iniciar fase de acciones (solo admin) o por sistema."""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        return
    # Solo el admin puede iniciarla manualmente
    is_admin = user_id == str(room.get("admin_id"))
    manual = message.get("manual", False)
    if manual and not is_admin:
        return

    allow_actions = bool(room.get("allow_actions", True))
    if not allow_actions:
        return

    # Duración
    seconds = 60 * int(room.get("action_time_minutes", 5) or 5)
    if isinstance(message.get("duration_seconds"), int) and message["duration_seconds"] > 0:
        seconds = message["duration_seconds"]

    # Reset estado de fase
    from datetime import datetime, timedelta
    deadline = (datetime.utcnow() + timedelta(seconds=seconds)).isoformat()
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$set": {
            "game_state": "action_phase",
            "pending_actions": [],
            "action_ready_players": [],
            "action_phase_deadline": deadline
        }}
    )

    # Cancelar tarea previa si existe
    if room_id in manager.action_phase_tasks:
        try:
            manager.action_phase_tasks[room_id].cancel()
        except Exception:
            pass

    # Lanzar tarea de conteo regresivo
    task = asyncio.create_task(_run_action_phase(room_id, seconds, db))
    manager.action_phase_tasks[room_id] = task

    # Broadcast inicial
    await broadcast_action_phase_update(room_id, db, time_remaining=seconds)

async def handle_submit_action(message: dict, room_id: str, user_id: str, username: str, db, accepted_from_ai: bool=False):
    """Recibir acción de jugador durante fase de acciones."""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room or room.get("game_state") != "action_phase":
        return
    # Hallar personaje del usuario
    char = None
    for sc in (room.get("selected_characters", []) or []):
        owner = sc.get("owner_id") or sc.get("user_id")
        if str(owner) == user_id:
            char = sc
            break
    if not char:
        return
    character_id = str(char.get("id") or char.get("character_id") or "")
    character_name = char.get("name") or char.get("character_name") or ""
    action_text = (message.get("action") or "").strip()
    if not action_text:
        return

    # Reemplazar acción previa del usuario
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$pull": {"pending_actions": {"user_id": user_id}}}
    )
    action_data = {
        "user_id": user_id,
        "username": username,
        "character_id": character_id,
        "character_name": character_name,
        "action": action_text,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "status": "pending",
        "accepted_from_ai": bool(accepted_from_ai)
    }
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$push": {"pending_actions": action_data}}
    )

    await broadcast_action_phase_update(room_id, db)
    # Aviso sutil al chat general
    try:
        await _rooms(db).update_one(
            {"_id": ObjectId(room_id)},
            {"$push": {"messages": {
                "user_id": user_id,
                "username": username,
                "message": "Acción registrada. Se evaluará en el siguiente capítulo.",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "message_type": "system"
            }}}
        )
        await manager.broadcast_to_room({
            "type": "new_message",
            "data": {
                "user_id": user_id,
                "username": username,
                "message": "Acción registrada. Se evaluará en el siguiente capítulo.",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "message_type": "system"
            }
        }, room_id)
    except Exception:
        pass

async def handle_mark_ready(room_id: str, user_id: str, db):
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room or room.get("game_state") != "action_phase":
        return
    await _rooms(db).update_one(
        {"_id": ObjectId(room_id)},
        {"$addToSet": {"action_ready_players": user_id}}
    )

    # Comprobar si todos listos
    updated = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    member_ids = [str(x) for x in (updated.get("member_ids", []) or [])]
    ready_ids = [str(x) for x in (updated.get("action_ready_players", []) or [])]
    await broadcast_action_phase_update(room_id, db)

    if len(member_ids) > 0 and set(member_ids) == set(ready_ids):
        # Todos listos: finalizar fase
        await _end_action_phase_and_generate(room_id, db)

async def broadcast_action_phase_update(room_id: str, db, time_remaining: Optional[int]=None):
    """Enviar estado de fase de acciones (tiempo y jugadores)."""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        return
    # Calcular tiempo restante
    remaining = time_remaining
    if remaining is None:
        remaining = _compute_time_remaining(room)

    # Construir lista de jugadores
    players_view = []
    # Mapa user_id->username
    users = {}
    for uid in (room.get("member_ids", []) or []):
        try:
            u = await _users(db).find_one({"_id": ObjectId(uid)})
            if u:
                users[str(u["_id"])]=u.get("username","")
        except Exception:
            continue
    ready_set = set([str(x) for x in (room.get("action_ready_players", []) or [])])
    actions_by_uid = {str(a.get("user_id")): a for a in (room.get("pending_actions", []) or [])}

    # Map user->character name
    char_name_by_uid = {}
    for sc in (room.get("selected_characters", []) or []):
        owner = str(sc.get("owner_id") or sc.get("user_id") or "")
        nm = sc.get("name") or sc.get("character_name") or ""
        char_name_by_uid[owner] = nm

    for uid in (room.get("member_ids", []) or []):
        uid_s = str(uid)
        action = actions_by_uid.get(uid_s)
        players_view.append({
            "username": users.get(uid_s, ""),
            "character": char_name_by_uid.get(uid_s, ""),
            "action": action.get("action") if action else None,
            "status": "ready" if uid_s in ready_set else "waiting"
        })

    await manager.broadcast_to_room({
        "type": "action_phase_update",
        "data": {
            "time_remaining": max(0, int(remaining)),
            "players": players_view
        }
    }, room_id)

def _compute_time_remaining(room: dict) -> int:
    from datetime import datetime
    deadline = room.get("action_phase_deadline")
    if not deadline:
        return 0
    try:
        end = datetime.fromisoformat(deadline)
        now = datetime.utcnow()
        return max(0, int((end - now).total_seconds()))
    except Exception:
        return 0

async def _run_action_phase(room_id: str, duration_seconds: int, db):
    """Tarea de conteo regresivo de fase de acciones."""
    try:
        remaining = duration_seconds
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
            # Emitir actualizaciones cada 3s para reducir ruido
            if remaining % 3 == 0 or remaining <= 5:
                await broadcast_action_phase_update(room_id, db, time_remaining=remaining)
        # Tiempo agotado
        await _end_action_phase_and_generate(room_id, db)
    except asyncio.CancelledError:
        return
    except Exception as e:
        print(f"[_run_action_phase] error: {e}")

async def _end_action_phase_and_generate(room_id: str, db):
    """Cierra fase y genera nuevo capítulo (con o sin acciones)."""
    room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if not room:
        return
    # Limpiar tarea registrada
    try:
        task = manager.action_phase_tasks.get(room_id)
        if task:
            task.cancel()
        manager.action_phase_tasks.pop(room_id, None)
    except Exception:
        pass

    # Preparar datos IA
    try:
        world_id = room.get("world_id")
        world = await db["worlds"].find_one({"_id": ObjectId(world_id)}) if world_id else None
    except Exception:
        world = None
    chapters = room.get("chapters", []) or []
    current_chapter = int(room.get("current_chapter", 0) or 0)
    max_chapters = int(room.get("max_chapters", 5) or 5)
    pending_actions = room.get("pending_actions", []) or []
    selected_chars = room.get("selected_characters", []) or []

    ai_service = AIService()
    new_num = current_chapter + 1
    if pending_actions:
        text = await ai_service.generate_chapter_with_actions(
            world=world or {},
            previous_chapters=chapters,
            player_actions=pending_actions,
            characters=selected_chars,
            total_chapters=max_chapters,
            chapter_index=new_num
        )
        actions_used = pending_actions
    else:
        text = await ai_service.generate_chapter_automatic(
            world=world or {},
            previous_chapters=chapters,
            characters=selected_chars,
            total_chapters=max_chapters,
            chapter_index=new_num
        )
        actions_used = []

    # Actualizar sala
    from datetime import datetime as _dt
    updates = {
        "$set": {
            "game_state": "playing",
            "current_chapter": new_num,
            "pending_actions": [],
            "action_ready_players": [],
            "action_phase_deadline": None,
            "continue_ready_players": []
        },
        "$push": {
            "chapters": text
        }
    }
    if new_num >= max_chapters:
        updates["$set"]["game_state"] = "finished"
    await _rooms(db).update_one({"_id": ObjectId(room_id)}, updates)

    # Notificar capítulo
    await manager.broadcast_to_room({
        "type": "chapter_update",
        "data": {
            "chapter_number": new_num,
            "text": text,
            "actions_used": actions_used
        }
    }, room_id)
    # Aviso sutil cuando no hay acciones
    if not actions_used:
        try:
            msg = {
                "user_id": str(room.get("admin_id", "")),
                "username": "Sistema",
                "message": "Continuando historia sin acciones sugeridas.",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "message_type": "system"
            }
            await _rooms(db).update_one({"_id": ObjectId(room_id)}, {"$push": {"messages": msg}})
            await manager.broadcast_to_room({"type": "new_message", "data": msg}, room_id)
        except Exception:
            pass
    updated = await get_room_data(room_id, db)
    if updated:
        await manager.broadcast_to_room({"type": "room_update", "data": updated}, room_id)

    # Si allow_actions sigue activo y no terminó, iniciar nueva fase automáticamente
    room2 = await _rooms(db).find_one({"_id": ObjectId(room_id)})
    if room2 and room2.get("game_state") == "playing" and bool(room2.get("allow_actions", True)) and new_num < max_chapters:
        await handle_start_action_phase({"manual": False}, room_id, str(room2.get("admin_id", "")), db)


# ========== Modo sin acciones: avance automático ==========
async def schedule_auto_mode(room_id: str, db):
    """Arranca modo automático (sin acciones), generando capítulos con una pausa entre ellos."""
    # Cancelar si ya hay uno
    if room_id in manager.auto_mode_tasks:
        try:
            manager.auto_mode_tasks[room_id].cancel()
        except Exception:
            pass
    task = asyncio.create_task(_run_auto_mode(room_id, db))
    manager.auto_mode_tasks[room_id] = task

async def _run_auto_mode(room_id: str, db):
    try:
        while True:
            room = await _rooms(db).find_one({"_id": ObjectId(room_id)})
            if not room:
                break
            # Salir si allow_actions se activó o juego terminó
            if bool(room.get("allow_actions", True)) or room.get("game_state") == "finished":
                break
            # Esperar delay
            delay = int(room.get("continue_time", DEFAULT_CONTINUE_TIME) or DEFAULT_CONTINUE_TIME)
            await asyncio.sleep(delay)
            # Generar siguiente capítulo
            await _end_action_phase_and_generate(room_id, db)
            # Verificar finalización
            room2 = await _rooms(db).find_one({"_id": ObjectId(room_id)})
            if not room2 or room2.get("game_state") == "finished":
                break
    except asyncio.CancelledError:
        return
    except Exception as e:
        print(f"[_run_auto_mode] error: {e}")
