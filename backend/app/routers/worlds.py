from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.models.schemas import WorldCreate, WorldPublic
from app.core.database import get_db
from bson import ObjectId
from datetime import datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _worlds(db):
    return db["worlds"]


def _users(db):
    return db["users"]


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
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/worlds", response_model=WorldPublic)
async def create_world(data: WorldCreate, db=Depends(get_db), user=Depends(get_current_user)):
    """Crear un nuevo mundo/serie"""
    doc = data.model_dump()
    doc.update({
        "creator_id": str(user["_id"]),
        "created_at": datetime.utcnow().isoformat(),
        "usage_count": 0
    })
    
    res = await _worlds(db).insert_one(doc)
    created = await _worlds(db).find_one({"_id": res.inserted_id})
    
    # Convertir ObjectId a string para evitar errores de serialización
    created["_id"] = str(created["_id"])
    created["id"] = created["_id"]
    
    return created


@router.get("/worlds")
async def list_worlds(db=Depends(get_db), user=Depends(get_current_user)):
    """Listar mundos del usuario y mundos públicos"""
    my_worlds = []
    public_worlds = []
    
    # Mundos del usuario
    async for world in _worlds(db).find({"creator_id": str(user["_id"])}):
        world["_id"] = str(world["_id"])
        world["id"] = world["_id"]
        my_worlds.append(world)
    
    # Mundos públicos de otros usuarios
    async for world in _worlds(db).find({
        "is_public": True, 
        "creator_id": {"$ne": str(user["_id"])}
    }).sort("usage_count", -1):
        world["_id"] = str(world["_id"])
        world["id"] = world["_id"]
        public_worlds.append(world)
    
    return {
        "my_worlds": my_worlds,
        "public_worlds": public_worlds
    }


@router.get("/worlds/public", response_model=list[WorldPublic])
async def list_public_worlds(db=Depends(get_db)):
    """Listar solo mundos públicos (sin autenticación)"""
    items = []
    async for world in _worlds(db).find({"is_public": True}).sort("usage_count", -1):
        world["_id"] = str(world["_id"])
        world["id"] = world["_id"]
        items.append(world)
    return items


@router.get("/worlds/{world_id}", response_model=WorldPublic)
async def get_world(world_id: str, db=Depends(get_db)):
    """Obtener detalles de un mundo específico"""
    try:
        world = await _worlds(db).find_one({"_id": ObjectId(world_id)})
        if not world:
            raise HTTPException(status_code=404, detail="Mundo no encontrado")
        
        world["_id"] = str(world["_id"])
        world["id"] = world["_id"]
        return world
    except Exception:
        raise HTTPException(status_code=404, detail="Mundo no encontrado")


@router.put("/worlds/{world_id}", response_model=WorldPublic)
async def update_world(world_id: str, data: WorldCreate, db=Depends(get_db), user=Depends(get_current_user)):
    """Actualizar un mundo (solo el creador)"""
    try:
        world = await _worlds(db).find_one({"_id": ObjectId(world_id)})
        if not world:
            raise HTTPException(status_code=404, detail="Mundo no encontrado")
        
        if world["creator_id"] != str(user["_id"]):
            raise HTTPException(status_code=403, detail="No tienes permisos para editar este mundo")
        
        update_data = data.model_dump()
        await _worlds(db).update_one(
            {"_id": ObjectId(world_id)},
            {"$set": update_data}
        )
        
        updated = await _worlds(db).find_one({"_id": ObjectId(world_id)})
        updated["_id"] = str(updated["_id"])
        updated["id"] = updated["_id"]
        return updated
        
    except Exception as e:
        if "403" in str(e) or "404" in str(e):
            raise e
        raise HTTPException(status_code=400, detail="Error al actualizar mundo")


@router.post("/worlds/{world_id}/use")
async def use_world(world_id: str, db=Depends(get_db)):
    """Incrementar contador de uso cuando se usa un mundo en una sala"""
    try:
        await _worlds(db).update_one(
            {"_id": ObjectId(world_id)},
            {"$inc": {"usage_count": 1}}
        )
        return {"message": "Contador actualizado"}
    except Exception:
        raise HTTPException(status_code=404, detail="Mundo no encontrado")


# Función para insertar mundos por defecto
async def insert_default_worlds(db):
    """Insertar mundos por defecto si no existen"""
    default_worlds = [
        {
            "title": "Reino de Eldoria",
            "summary": "Un reino medieval mágico donde coexisten humanos, elfos y enanos. Dragones legendarios protegen territorios sagrados.",
            "context": "Eldoria es un vasto reino dividido en cinco ducados. La magia es común pero regulada por la Academia de Magos. Las criaturas mágicas viven en armonía con los humanos en la mayoría de regiones.",
            "logic": "Magia elemental (fuego, agua, tierra, aire) disponible para algunos individuos. Criaturas mágicas existen. Tecnología medieval con toques mágicos.",
            "time_period": "Medieval mágico",
            "space_setting": "Fantasía épica",
            "is_public": True,
            "allow_action_suggestions": True,
            "creator_id": "system",
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        },
        {
            "title": "Neo-Tokyo 2087",
            "summary": "Una metrópolis cyberpunk donde la tecnología y la humanidad chocan. Corporaciones controlan la ciudad mientras hackers luchan por la libertad.",
            "context": "Neo-Tokyo es una megaciudad estratificada. Los ricos viven en torres de cristal mientras los pobres habitan el subsuelo. La IA ha reemplazado muchos trabajos humanos.",
            "logic": "Tecnología avanzada: implantes cibernéticos, inteligencia artificial, realidad virtual. Sin poderes sobrenaturales, solo tecnología.",
            "time_period": "Futuro distópico (2087)",
            "space_setting": "Cyberpunk urbano",
            "is_public": True,
            "allow_action_suggestions": True,
            "creator_id": "system",
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        },
        {
            "title": "Academia Supernatural",
            "summary": "Una escuela secreta donde jóvenes con habilidades sobrenaturales aprenden a controlar sus poderes mientras enfrentan amenazas ocultas.",
            "context": "La Academia Blackwood está oculta del mundo normal. Estudiantes con poderes psíquicos, control elemental, y otras habilidades estudian aquí. Amenazas demoníacas acechan.",
            "logic": "Poderes psíquicos, control elemental, telequinesis, lectura mental. Criaturas sobrenaturales y demonios existen. Mundo moderno con elementos ocultos.",
            "time_period": "Contemporáneo",
            "space_setting": "Urbano fantasía moderna",
            "is_public": True,
            "allow_action_suggestions": True,
            "creator_id": "system",
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        },
        {
            "title": "El Salvaje Oeste",
            "summary": "Tierras fronterizas donde forajidos, sheriffs y colonos luchan por sobrevivir en un mundo sin ley.",
            "context": "Año 1875, territorio de Arizona. Pequeños pueblos mineros, trenes que cruzan el desierto, y la ley del más fuerte. Conflictos entre colonos, nativos americanos y bandidos.",
            "logic": "Mundo realista sin magia. Tecnología del siglo XIX: revólveres, rifles, caballos, telégrafos. Supervivencia y honor son clave.",
            "time_period": "Siglo XIX (1875)",
            "space_setting": "Western americano",
            "is_public": True,
            "allow_action_suggestions": True,
            "creator_id": "system",
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        },
        {
            "title": "Espacio Profundo: Estación Omega",
            "summary": "Una estación espacial en los confines de la galaxia donde diferentes especies alienígenas coexisten mientras exploran lo desconocido.",
            "context": "Estación Omega es un punto de encuentro intergaláctico. Especies de toda la galaxia comercian, investigan y exploran desde aquí. Peligros cósmicos acechan en el espacio profundo.",
            "logic": "Tecnología espacial avanzada: viaje FTL, armas de energía, campos de fuerza. Múltiples especies alienígenas con diferentes habilidades naturales.",
            "time_period": "Futuro lejano (Año 2847)",
            "space_setting": "Ciencia ficción espacial",
            "is_public": True,
            "allow_action_suggestions": True,
            "creator_id": "system",
            "created_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        }
    ]
    
    worlds_collection = _worlds(db)
    
    for world_data in default_worlds:
        # Verificar si ya existe un mundo con el mismo título
        existing = await worlds_collection.find_one({"title": world_data["title"]})
        if not existing:
            await worlds_collection.insert_one(world_data)
