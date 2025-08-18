# KandaStory Backend

FastAPI + MongoDB backend para KandaStory.

## Requisitos Previos

- Python 3.8+
- MongoDB Atlas account (o MongoDB local)
- OpenAI API Key
- Gmail account para envío de emails (opcional)

## Configuración Inicial

### 1. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crear archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

**Variables de entorno requeridas:**

```env
# FastAPI
APP_NAME=KandaStory
API_PREFIX=/api
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174

# MongoDB - OBLIGATORIO
DB_URI=mongodb+srv://<USER>:<PASSWORD>@<CLUSTER>/<DB_NAME>?retryWrites=true&w=majority
DB_NAME=kandastory

# JWT - OBLIGATORIO (cambiar en producción)
JWT_SECRET=tu_clave_jwt_secreta_muy_segura_aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email (Gmail SMTP) - OPCIONAL
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password
DEFAULT_FROM_EMAIL=tu_email@gmail.com

# OpenAI - OBLIGATORIO
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```

### 4. Configurar MongoDB

1. Crear cuenta en [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Crear un cluster
3. Crear un usuario de base de datos
4. Obtener la cadena de conexión
5. Reemplazar `<USER>`, `<PASSWORD>` y `<CLUSTER>` en `DB_URI`

### 5. Configurar OpenAI

1. Crear cuenta en [OpenAI](https://platform.openai.com/)
2. Generar API Key
3. Agregar la API Key en `OPENAI_API_KEY`

## Ejecución

### Desarrollo

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Ejecutar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Verificación

Una vez ejecutado, el backend estará disponible en:

- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

## Conexión con Frontend

El frontend debe configurar `VITE_API_BASE_URL=http://127.0.0.1:8000` en su archivo `.env`

## Troubleshooting

### Error de conexión MongoDB
- Verificar que `DB_URI` sea correcta
- Verificar conectividad de red
- Verificar credenciales de usuario

### Error de CORS
- Verificar que el origen del frontend esté en `BACKEND_CORS_ORIGINS`
- Verificar que no haya espacios extra en la configuración

### Error de OpenAI
- Verificar que `OPENAI_API_KEY` sea válida
- Verificar créditos disponibles en la cuenta OpenAI

## API Endpoints

### Autenticación
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Inicio de sesión
- `POST /api/auth/verify-email` - Verificación de email

### Personajes
- `GET /api/characters` - Listar personajes del usuario
- `POST /api/characters` - Crear personaje
- `PUT /api/characters/{character_id}` - Actualizar personaje
- `DELETE /api/characters/{character_id}` - Eliminar personaje

### Mundos
- `GET /api/worlds` - Listar mundos disponibles
- `POST /api/worlds` - Crear mundo personalizado

### Salas de Juego
- `GET /api/rooms` - Listar salas
- `POST /api/rooms` - Crear sala
- `POST /api/rooms/{room_id}/join` - Unirse a sala
- `POST /api/rooms/{room_id}/chapter` - Crear capítulo
- `POST /api/rooms/{room_id}/suggest` - Sugerir acción

### WebSockets
- `WS /api/websocket/{room_id}` - Conexión en tiempo real para salas
