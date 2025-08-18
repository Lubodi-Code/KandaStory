from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import close_db
from app.routers import auth, characters, rooms, worlds, websockets, games, connectivity

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API para KandaStory - Plataforma de narrativa colaborativa con IA",
    version="1.0.0"
)

# CORS Configuration - IMPORTANTE: Debe ir ANTES de los routers
origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(',') if o.strip()]
# Fallback seguro en desarrollo si no hay orígenes configurados
if not origins:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
print(f"🔧 CORS configurado para: {origins}")

# Configuración más permisiva para desarrollo
app.add_middleware(
    CORSMiddleware,
    # Importante: con allow_credentials=True no se puede usar "*"
    # Usamos la lista proveniente de la configuración para desarrollo
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Routers
app.include_router(auth.router, prefix=settings.API_PREFIX, tags=["auth"])
app.include_router(characters.router, prefix=settings.API_PREFIX, tags=["characters"])
app.include_router(rooms.router, prefix=settings.API_PREFIX, tags=["rooms"])
app.include_router(worlds.router, prefix=settings.API_PREFIX, tags=["worlds"])
app.include_router(websockets.router, prefix=settings.API_PREFIX, tags=["websockets"])
app.include_router(games.router)
app.include_router(connectivity.router, prefix=settings.API_PREFIX, tags=["connectivity"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": settings.API_PREFIX
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "database": "connected",  # TODO: Add actual DB health check
        "cors_origins": origins,
        "api_prefix": settings.API_PREFIX
    }

@app.on_event("startup")
async def startup_event():
    """Eventos de inicio de la aplicación"""
    print(f"🚀 Iniciando {settings.APP_NAME}")
    print(f"📖 Documentación disponible en: /docs")
    print(f"🔧 API Prefix: {settings.API_PREFIX}")
    print(f"🌐 CORS Origins: {origins}")
    
    # Insertar mundos por defecto al iniciar la aplicación
    try:
        from app.core.database import get_db
        from app.routers.worlds import insert_default_worlds
        db = await get_db()
        await insert_default_worlds(db)
        print("✅ Mundos por defecto inicializados")

        # Ensure indexes for normalized game collections
        try:
            await db["game_members"].create_index("game_id")
            await db["game_messages"].create_index("game_id")
            await db["game_actions"].create_index("game_id")
            await db["game_chapters"].create_index("game_id")
            print("✅ Índices creados para colecciones de juegos (game_id)")
        except Exception as ie:
            print(f"⚠️  Error creando índices: {ie}\n")
    except Exception as e:
        print(f"⚠️  Error inicializando mundos por defecto: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos de cierre de la aplicación"""
    print("🛑 Cerrando conexiones de base de datos...")
    await close_db()
    print("✅ Aplicación cerrada correctamente")
