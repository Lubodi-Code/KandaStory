---
mode: ask
---
You are an AI agent embedded in the KandaStory project. Use the following context to understand the architecture, workflows, and constraints before performing any task.  

## Goal
Assist in developing, debugging, and extending KandaStory — a monorepo game storytelling platform — ensuring code changes respect architecture, conventions, and security.

## Project Context
- **Monorepo**:  
  - `backend/` → FastAPI + MongoDB + OpenAI.  
  - `frontend/` → Vue 3 + TypeScript + Pinia + Vite.  
- **Backend**:  
  - Entry: `backend/app/main.py` mounts routers with `API_PREFIX` (default `/api`) for `auth`, `characters`, `rooms`, `worlds`, `websockets`, and `games`. Legacy `gamerooms` is removed.  
  - CORS: set from `.env` `BACKEND_CORS_ORIGINS`.  
  - Models: `backend/app/models/schemas.py` (Pydantic v2). All `ObjectId` → `str` in responses.  
  - DB: `backend/app/core/database.py` (Motor singletons).  
  - Auth: `backend/app/core/security.py` (bcrypt, JWT). Protected endpoints require OAuth2 bearer.  
  - AI: `backend/app/services/ai_service.py` uses `openai` Chat Completions. Model from `OPENAI_MODEL` (`gpt-4o-mini` default).  
  - WebSocket: `/api/ws/{room_id}?token=...` sends `room_update`, `new_message`, `ready_update`, `game_state_change`, `character_selected`.

- **Frontend**:  
  - Axios in `frontend/src/lib/api.ts`: baseURL = `${VITE_API_BASE_URL}/api`, sends Bearer token, redirects on 401.  
  - API services in `frontend/src/api/*.ts`.  
  - WebSocket: `${VITE_WS_BASE_URL}/api/ws/${roomId}?token=${token}`.  
  - Auth store persists token/user and refreshes `/auth/me`.

## Dev workflows
- Backend: `.env` from `.env.example`, run Uvicorn or `backend/start_backend.bat`. Health: `GET /`, Docs: `/docs`.  
- Frontend: `.env` with `VITE_API_BASE_URL` & `VITE_WS_BASE_URL`, `npm install && npm run dev`.

## Conventions
- Respect `settings.API_PREFIX`.  
- Explicit CORS origins (no `*` with `allow_credentials=True`).  
- Always JSON-safe data (convert `ObjectId`).  
- Room logic: `member_ids` and `members` sync; only `admin_id` can generate chapters.  
- WebSocket payload: `{ type, data }`. Client messages:  
  - `chat_message` → { message, message_type? }  
  - `toggle_ready` → no payload  
  - `select_character` → { character_id }  

## Integration Notes
- Prefer `AIService().generate_first_chapter(...)` and `generate_chapter_with_actions(...)`.  
- `frontend/src/api/ApiGame.ts` has optimistic endpoints not implemented in backend — use existing `/rooms`, `/rooms/{id}/*`, and WebSocket for readiness/game state.  
- Duplicate `get_my_room` in `rooms.py` — be careful merging.

## Your Role
When asked for a task:
1. Use above architecture to propose correct file changes.
2. Suggest minimal, maintainable, and secure edits.
3. Ensure code matches framework idioms (FastAPI, Vue 3 + Pinia + Tailwind).
4. For new features, define both backend and frontend integration steps.
5. For debugging, give exact file paths, line numbers, and fix proposals.

Do not remove or ignore project-specific guardrails.
