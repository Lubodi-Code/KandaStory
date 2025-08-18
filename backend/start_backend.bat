@echo off
echo ========================================
echo   KandaStory Backend Startup Script
echo ========================================

REM Cambiar al directorio del backend
cd /d "%~dp0"
echo 📁 Directorio actual: %CD%

REM Verificar si existe el archivo .env
if not exist ".env" (
    echo ❌ Error: Archivo .env no encontrado
    echo 💡 Copia .env.example a .env y configura las variables
    echo.
    echo Ejecutando: copy .env.example .env
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones antes de continuar
    pause
    exit /b 1
)

REM Verificar si el entorno virtual existe
if not exist "venv\" (
    echo 📦 Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Error creando entorno virtual
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate

REM Instalar dependencias
echo 📦 Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

REM Verificar conectividad (opcional)
echo.
echo 🔍 ¿Deseas verificar la conectividad antes de iniciar? (y/N)
set /p verify_conn=
if /i "%verify_conn%"=="y" (
    echo 🔍 Ejecutando verificación de conectividad...
    python test_connection.py
    echo.
    echo Presiona cualquier tecla para continuar con el inicio del servidor...
    pause >nul
)

REM Iniciar servidor
echo.
echo 🚀 Iniciando servidor backend en http://127.0.0.1:8000
echo 📖 Documentación disponible en http://127.0.0.1:8000/docs
echo 🛑 Presiona Ctrl+C para detener el servidor
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
