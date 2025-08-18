from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.models.schemas import CharacterCreate, CharacterPublic, CharacterEvaluation
from app.core.database import get_db
from app.services.ai_service import evaluate_character
from bson import ObjectId

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _characters(db):
    return db["characters"]


def _users(db):
    return db["users"]


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    # Minimal token check (in a real app decode and verify JWT)
    from app.core.security import decode_token
    try:
        payload = decode_token(token)
        uid = payload.get("sub")
        user = await _users(db).find_one({"_id": ObjectId(uid)})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/characters/evaluate", response_model=CharacterEvaluation)
async def evaluate_character_endpoint(data: CharacterCreate, user=Depends(get_current_user)):
    """Evalúa un personaje y devuelve sugerencias de mejora"""
    character_dict = data.model_dump()
    ai_result = evaluate_character(character_dict)
    
    return CharacterEvaluation(
        evaluation_text=ai_result.get("evaluation_summary", "Evaluación completada"),
        suggested_corrections=CharacterCreate(**ai_result.get("corrected_character", character_dict)),
        needs_improvement=ai_result.get("needs_improvement", False)
    )

@router.post("/characters", response_model=CharacterPublic)
async def create_character(data: CharacterCreate, db=Depends(get_db), user=Depends(get_current_user)):
    """Crea un personaje directamente sin evaluación"""
    doc = data.model_dump()
    doc.update({"owner_id": str(user["_id"])})
    
    # No evaluación automática, solo crear el personaje
    res = await _characters(db).insert_one(doc)
    created = await _characters(db).find_one({"_id": res.inserted_id})
    created["_id"] = str(created["_id"])
    return created


@router.get("/characters", response_model=list[CharacterPublic])
async def list_my_characters(db=Depends(get_db), user=Depends(get_current_user)):
    items = []
    async for ch in _characters(db).find({"owner_id": str(user["_id"])}):
        ch["_id"] = str(ch["_id"]) 
        items.append(ch)
    return items
