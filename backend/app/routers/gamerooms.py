from fastapi import APIRouter, HTTPException

# Deprecated: 'gamerooms' has been removed in favor of rooms (lobby) + games (normalized game state).
# This stub exists only to return 410 Gone for any accidental calls during migration.
router = APIRouter(prefix="/api/gamerooms", tags=["gamerooms"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])  # type: ignore[misc]
async def deprecated_gamerooms_proxy(path: str):
    raise HTTPException(status_code=410, detail="'gamerooms' API has been removed. Use /api/rooms (lobby) and /api/games (game state).")
