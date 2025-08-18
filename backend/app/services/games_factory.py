from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from bson import ObjectId

# Fallback default for continue timers (seconds)
DEFAULT_CONTINUE_TIME = 60


async def create_game_from_room(db, room_id: str) -> str:
    """Create a normalized Game from a lobby Room.

    - Reads the room from collection 'rooms'.
    - Creates a document in 'games' with basic meta and settings.
    - Snapshots room members into 'game_members'.
    - Links the room with the created game_id and marks state as in-game/playing.
    - If a game already exists for the room, returns the existing game_id.
    """
    try:
        room = await db["rooms"].find_one({"_id": ObjectId(room_id)})
    except Exception:
        room = None
    if not room:
        raise ValueError("Room not found")

    # Guard against duplicates
    if room.get("game_id"):
        return str(room["game_id"]) if not isinstance(room["game_id"], ObjectId) else str(room["game_id"])

    # Normalize settings from room
    settings = {
        "allow_suggestions": bool(room.get("allow_actions", room.get("allow_suggestions", True))),
        "discussion_time": int(room.get("discussion_time", 300) or 300),
        "auto_continue": bool(room.get("auto_continue", False)),
        "continue_time": int(room.get("continue_time", DEFAULT_CONTINUE_TIME) or DEFAULT_CONTINUE_TIME),
    }

    owner = room.get("owner_id") or room.get("admin_id")
    admin = room.get("admin_id")

    game_doc: Dict[str, Any] = {
        "room_id": str(room.get("_id")),
        "name": room.get("name", ""),
        "world_id": str(room.get("world_id") or ""),
        "max_chapters": int(room.get("max_chapters", 5) or 5),
        "max_players": int(room.get("max_players", 4) or 4),
        "settings": settings,
        "owner_id": str(owner) if owner is not None else None,
        "admin_id": str(admin) if admin is not None else None,
        "current_chapter": 0,
        "game_state": "playing",
        "created_at": datetime.utcnow().isoformat(),
    }

    res = await db["games"].insert_one(game_doc)
    game_id = res.inserted_id

    # Members snapshot
    members = room.get("members", []) or []
    if not members:
        # fallback to member_ids if members array not populated
        members = [{"user_id": mid} for mid in (room.get("member_ids", []) or [])]

    bulk = []
    for m in members:
        uid = str(m.get("user_id") or m)
        bulk.append({
            "game_id": str(game_id),
            "user_id": uid,
            "character_id": m.get("selected_character_id") or None,
            "role": "admin" if uid == str(admin) else "player",
            "joined_at": datetime.utcnow().isoformat(),
            "is_ready": True,
        })
    if bulk:
        await db["game_members"].insert_many(bulk)

    # Link back to room and update state
    await db["rooms"].update_one(
        {"_id": room["_id"]},
        {"$set": {"status": "in_game", "game_state": "playing", "game_id": str(game_id)}}
    )

    return str(game_id)
