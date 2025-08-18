#!/usr/bin/env python3
"""
Script de verificación de conectividad para KandaStory Backend
Ejecutar este script para verificar que todas las conexiones funcionen correctamente.
"""

import os
import sys
import asyncio
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def test_mongodb_connection():
    """Probar conexión a MongoDB"""
    print("🔗 Probando conexión a MongoDB...")
    try:
        db_uri = os.getenv("DB_URI")
        if not db_uri:
            print("❌ DB_URI no está configurado en .env")
            return False
        
        client = AsyncIOMotorClient(db_uri)
        # Probar la conexión
        await client.admin.command('ping')
        print("✅ Conexión a MongoDB exitosa")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return False

async def test_backend_health():
    """Probar que el backend esté respondiendo"""
    print("🔗 Probando salud del backend...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8000/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Backend respondiendo: {data}")
                    return True
                else:
                    print(f"❌ Backend responde con código: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        print("   💡 Asegúrate de que el backend esté ejecutándose en puerto 8000")
        return False

def test_openai_config():
    """Verificar configuración de OpenAI"""
    print("🔗 Verificando configuración de OpenAI...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY no está configurado en .env")
        return False
    elif not api_key.startswith("sk-"):
        print("❌ OPENAI_API_KEY no tiene formato válido (debe empezar con 'sk-')")
        return False
    else:
        print("✅ OPENAI_API_KEY configurado correctamente")
        return True

def test_jwt_config():
    """Verificar configuración de JWT"""
    print("🔗 Verificando configuración de JWT...")
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        print("❌ JWT_SECRET no está configurado en .env")
        return False
    elif jwt_secret == "change-me" or len(jwt_secret) < 32:
        print("⚠️  JWT_SECRET debería ser más seguro (mínimo 32 caracteres)")
        return False
    else:
        print("✅ JWT_SECRET configurado correctamente")
        return True

def test_cors_config():
    """Verificar configuración de CORS"""
    print("🔗 Verificando configuración de CORS...")
    cors_origins = os.getenv("BACKEND_CORS_ORIGINS")
    if not cors_origins:
        print("❌ BACKEND_CORS_ORIGINS no está configurado en .env")
        return False
    
    origins = [o.strip() for o in cors_origins.split(',') if o.strip()]
    frontend_urls = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    
    missing_origins = []
    for url in frontend_urls:
        if url not in origins:
            missing_origins.append(url)
    
    if missing_origins:
        print(f"⚠️  CORS: Faltan orígenes para el frontend: {missing_origins}")
        print(f"   Configuración actual: {origins}")
        return False
    else:
        print("✅ CORS configurado correctamente para el frontend")
        return True

async def main():
    """Función principal de verificación"""
    print("🚀 KandaStory Backend - Verificación de Conectividad")
    print("=" * 60)
    
    # Verificar archivo .env
    if not os.path.exists(".env"):
        print("❌ Archivo .env no encontrado")
        print("   💡 Copiar .env.example a .env y configurar las variables")
        return
    
    tests = [
        ("Configuración JWT", test_jwt_config),
        ("Configuración CORS", test_cors_config),
        ("Configuración OpenAI", test_openai_config),
        ("Conexión MongoDB", test_mongodb_connection),
        ("Salud del Backend", test_backend_health),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results.append((test_name, result))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las verificaciones pasaron! El backend debería funcionar correctamente.")
    else:
        print("⚠️  Hay problemas que deben resolverse antes de que el backend funcione correctamente.")
        print("💡 Revisa la documentación en README.md para más detalles.")

if __name__ == "__main__":
    asyncio.run(main())
