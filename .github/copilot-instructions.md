# KandaStory — AI agent working notes

Goal: give AI agents concise, project-specific context to work productively here.

## Architecture (big picture)
- Monorepo: `backend/` (FastAPI + MongoDB + OpenAI) and `frontend/` (Vue 3 + TS + Pinia + Vite).
- Backend entry `backend/app/main.py`: mounts routers with `API_PREFIX` (default `/api`): `auth`, `characters`, `rooms`, `worlds`, `websockets`, and `games`. The legacy `gamerooms` router is no longer mounted. CORS set before routers from `.env` `BACKEND_CORS_ORIGINS`.
- Data/DB: `backend/app/models/schemas.py` (Pydantic v2) and `backend/app/core/database.py` (Motor singletons). Convert any `ObjectId` to `str` in responses (validators + `_to_serializable`).
- Auth: `backend/app/core/security.py` (bcrypt, JWT create/decode/verify). Most protected endpoints depend on OAuth2 bearer token.
- AI: `backend/app/services/ai_service.py` uses `openai` Chat Completions; model via `OPENAI_MODEL` (default `gpt-4o-mini`).
- Realtime: `backend/app/routers/websockets.py` exposes `/api/ws/{room_id}?token=...` for lobby updates and `/api/ws/game/{game_id}?token=...` for in-game updates. Room channel events: `room_update`, `new_message`, `ready_update`, `game_state_change`, `character_selected`, `room:started`. Game channel events: `game:chapter_created`, `game:actions_updated`, `game:continue_update`.

## Frontend integration
- Axios setup in `frontend/src/lib/api.ts`: `baseURL=${VITE_API_BASE_URL}/api`, sends `Authorization: Bearer <token>` from `localStorage`, redirects to `/login` on 401.
- API services in `frontend/src/api/*.ts` wrap endpoints; `ApiGame#createWebSocket(roomId, token)` builds `${VITE_WS_BASE_URL}/api/ws/${roomId}?token=${token}`.
- Auth store `frontend/src/stores/auth.ts` persists token/user and refreshes `/auth/me` on boot.

## Dev workflows (daily-driving)
- Backend: copy `.env.example` → `.env`, then run Uvicorn (`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`). On Windows, `backend/start_backend.bat` handles venv + deps + optional `test_connection.py` (checks Mongo/JWT/CORS/OpenAI). Health: `GET /`, docs: `/docs`.
- Frontend: create `frontend/.env` with `VITE_API_BASE_URL=http://127.0.0.1:8000` and `VITE_WS_BASE_URL=ws://127.0.0.1:8000`, then `npm install && npm run dev`.

## Conventions and guardrails
- Respect `settings.API_PREFIX`; keep CORS origins explicit (no `*` with `allow_credentials=True`).
- Always return JSON-safe data (no raw `ObjectId`); reuse validators and `_to_serializable`.
- Rooms: maintain both `member_ids` (strings) and `members` on join/leave; only `admin_id` may generate chapters; public lists: `/api/worlds/public`, `/api/rooms/public`.
- WebSocket payloads: send a `type` and minimal `data`. Supported client messages include `chat_message` ({ message, message_type? }), `toggle_ready` (no payload), `select_character` ({ character_id }).

## Integration notes (project-specific gotchas)
- ai_service has two `generate_story_chapter` defs (legacy sync and newer async). Prefer `AIService().generate_first_chapter(...)` and `generate_chapter_with_actions(...)` in new code.
- `frontend/src/api/ApiGame.ts` includes optimistic endpoints (`PUT/DELETE /rooms`, `/toggle-ready`, `/start`) not implemented in `rooms.py`. Use existing HTTP routes (`/rooms`, `/rooms/{id}/join|leave|select-character|suggest|chapter`) and drive readiness/game state over WebSocket.
- `rooms.py` contains duplicate `get_my_room` definitions; consolidate carefully if editing.

Refs: `backend/app/routers/*`, `backend/app/models/schemas.py`, `backend/app/core/*`, `frontend/src/api/*`, `frontend/src/stores/auth.ts`, `backend/test_connection.py`.
