# Guía de Solución de Problemas - KandaStory Backend

## Problema: Frontend no se puede conectar al Backend

### Verificaciones Rápidas

1. **¿Está ejecutándose el backend?**
   ```bash
   # Windows
   netstat -an | findstr ":8000"
   
   # Debería mostrar: TCP 0.0.0.0:8000 ... LISTENING
   ```

2. **¿Responde el backend?**
   ```bash
   # En PowerShell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get
   
   # Debería devolver: {"status":"ok","service":"KandaStory",...}
   ```

3. **¿Está configurado correctamente el frontend?**
   - Verificar `frontend/.env`:
     ```env
     VITE_API_BASE_URL=http://127.0.0.1:8000
     ```

### Problemas Comunes y Soluciones

#### Error: "Access to fetch at '...' from origin '...' has been blocked by CORS policy"

**Causa:** Configuración de CORS incorrecta

**Solución:**
1. Verificar `backend/.env`:
   ```env
   BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174
   ```

2. Asegurar que no hay espacios extra en la configuración

3. Reiniciar el backend después de cambios en `.env`

#### Error: "Connection refused" o "ERR_CONNECTION_REFUSED"

**Causas posibles:**
- Backend no está ejecutándose
- Puerto 8000 ocupado por otro proceso
- Firewall bloqueando conexiones

**Soluciones:**
1. Verificar que el backend esté ejecutándose:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Si el puerto está ocupado, usar otro puerto:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
   ```
   Y actualizar el frontend `.env`:
   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8001
   ```

#### Error: "Module not found" al iniciar el backend

**Causa:** Dependencias no instaladas o entorno virtual no activado

**Solución:**
1. Activar entorno virtual:
   ```bash
   # Windows
   venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

#### Error: "ValidationError" para variables de entorno

**Causa:** Variables requeridas no están configuradas en `.env`

**Solución:**
1. Verificar que existe `backend/.env`
2. Copiar desde ejemplo si no existe:
   ```bash
   copy .env.example .env
   ```
3. Configurar variables obligatorias:
   - `DB_URI`: Conexión a MongoDB
   - `JWT_SECRET`: Clave secreta para JWT
   - `OPENAI_API_KEY`: Clave de OpenAI

#### Error de conexión a MongoDB

**Causa:** Credenciales incorrectas o red

**Solución:**
1. Verificar `DB_URI` en `.env`
2. Probar conexión con script:
   ```bash
   python test_connection.py
   ```
3. Verificar credenciales en MongoDB Atlas

### Comandos de Diagnóstico

#### Verificar estado completo:
```bash
cd backend
python test_connection.py
```

#### Verificar puertos en uso:
```bash
# Windows
netstat -an | findstr ":8000\|:5173"

# Linux/Mac
netstat -an | grep ":8000\|:5173"
```

#### Verificar procesos Python:
```bash
# Windows
Get-Process -Name "python*" -ErrorAction SilentlyContinue

# Linux/Mac
ps aux | grep python
```

#### Verificar logs del backend:
Los logs aparecen en la consola donde se ejecuta uvicorn. Buscar errores como:
- `ValidationError`: Variables de entorno faltantes
- `ConnectionError`: Problemas de base de datos
- `ImportError`: Dependencias faltantes

### Inicio Limpio del Sistema

1. **Detener todos los procesos:**
   ```bash
   # Ctrl+C en terminales activos
   # O cerrar todas las ventanas de terminal
   ```

2. **Backend:**
   ```bash
   cd backend
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   python test_connection.py
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend (en otra terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### URLs de Verificación

Una vez ejecutándose ambos servicios:

- **Backend Health:** http://127.0.0.1:8000/
- **Backend API Docs:** http://127.0.0.1:8000/docs
- **Frontend:** http://localhost:5173/

### Contacto de Soporte

Si los problemas persisten:
1. Ejecutar `python test_connection.py` y enviar resultados
2. Incluir logs de error completos
3. Especificar sistema operativo y versión de Python
