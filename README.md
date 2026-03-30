# Task Manager AI

Aplicación full-stack de gestión de tareas con chat IA, tool-calling real sobre CRUD y resumen diario asistido por IA.

## Stack

- Backend: FastAPI, SQLAlchemy async, Alembic, PostgreSQL (Neon), Pydantic, OpenAI SDK (compatible con DeepSeek)
- Frontend: React, Vite, TypeScript, Tailwind
- AI: provider compatible con OpenAI API (DeepSeek), con fallback controlado

## Requisitos previos

Instala lo siguiente en tu máquina:

1. Python 3.14
2. Pipenv
3. Node.js 20+ y npm
4. PostgreSQL o cuenta Neon

Comandos (PowerShell) para verificar:

```powershell
python --version
pipenv --version
node --version
npm --version
```

## Estructura de proyecto

- Root: scripts de orquestación y documentación
- backend: API, modelos, migraciones, integración IA
- frontend: UI y cliente HTTP

## Variables de entorno

Nunca hardcodees secretos. Usa archivos .env locales y no subas claves reales al repositorio.

### Backend: archivo backend/.env

Ejemplo completo:

```ini
APP_NAME=task-ai-manager
APP_ENV=development
APP_DEBUG=true
APP_CORS_ALLOW_ALL_DEV=true
API_PREFIX=/api
APP_HOST=0.0.0.0
APP_PORT=8010
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:8010
FRONTEND_URL=http://localhost:5174
BACKEND_URL=http://localhost:8010

# Database
DATABASE_URL=postgresql://user:pass@host-pooler/db?sslmode=require&channel_binding=require
# Opcional para migraciones (directa, no pooler)
DIRECT_DATABASE_URL=postgresql://user:pass@host-direct/db?sslmode=require&channel_binding=require

# AI Provider
AI_ENABLED=true
AI_PROVIDER=deepseek
AI_MODEL=deepseek-chat
AI_API_KEY=replace_me
AI_BASE_URL=https://api.deepseek.com
AI_TIMEOUT_SECONDS=30
AI_ALLOW_FALLBACK=true

# Compat Anthropic opcional
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_API_KEY=replace_me
ANTHROPIC_MODEL=deepseek-chat
```

### Frontend: archivo frontend/.env

```ini
VITE_API_BASE_URL=http://127.0.0.1:8010
```

### Root: archivo .env (opcional)

Solo si quieres centralizar algunas variables de referencia para scripts/documentación.

## Instalación completa

### 1) Instalar dependencias de root

```powershell
cd c:/Proyectos/Prueba_Projectus
npm install
```

### 2) Instalar backend

```powershell
cd c:/Proyectos/Prueba_Projectus/backend
pipenv install
```

### 3) Instalar frontend

```powershell
cd c:/Proyectos/Prueba_Projectus/frontend
npm install
```

## Inicialización de base de datos

Con backend/.env configurado:

```powershell
cd c:/Proyectos/Prueba_Projectus/backend
pipenv run migrate
```

Notas:

- DATABASE_URL se usa en runtime de API
- DIRECT_DATABASE_URL se usa para migraciones si está definido

## Arranque en desarrollo

Recomendado en terminales separadas.

### Backend

```powershell
cd c:/Proyectos/Prueba_Projectus/backend
pipenv run start
```

### Frontend

```powershell
cd c:/Proyectos/Prueba_Projectus/frontend
npm run dev -- --host 0.0.0.0 --port 5174
```

### Opción desde root

```powershell
cd c:/Proyectos/Prueba_Projectus
npm run dev
```

## Endpoints principales

Health:

- GET /health
- GET /api/health
- GET /ai/health
- GET /api/ai/health
- GET /db/health
- GET /api/db/health

Chat:

- POST /ai/chat
- POST /api/ai/chat
- POST /api/ai/test (prueba real de provider)

Tasks:

- GET /api/tasks
- POST /api/tasks
- GET /api/tasks/:id
- PATCH /api/tasks/:id
- PATCH /api/tasks/:id/complete
- DELETE /api/tasks/:id

Summary:

- GET /api/summary/today

## Verificación rápida (smoke test)

### 1) Health general

```powershell
Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8010/health
```

### 2) Health IA real

```powershell
Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8010/ai/health?probe=true | ConvertTo-Json -Depth 8
```

### 3) Health DB

```powershell
Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8010/db/health | ConvertTo-Json -Depth 8
```

### 4) Prueba real de DeepSeek

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8010/api/ai/test -ContentType "application/json" -Body '{"message":"responde solo OK"}' | ConvertTo-Json -Depth 8
```

### 5) Crear tarea por chat (tool-calling)

```powershell
$payload = '{"message":"crea una tarea llamada demo desde chat para 2099-06-01T09:00:00Z con prioridad high","session_id":"smoke-chat"}'
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8010/api/ai/chat -ContentType "application/json" -Body $payload | ConvertTo-Json -Depth 12
```

## Contrato de respuesta del chat

Ejemplo de éxito:

```json
{
  "data": {
    "success": true,
    "provider_available": true,
    "fallback_mode": false,
    "answer": "Task created successfully...",
    "actions": [
      {
        "tool_name": "create_task",
        "arguments": { "title": "..." },
        "result": { "task": { "id": 123, "status": "pending" } }
      }
    ],
    "tasks_changed": [
      { "id": 123, "operation": "create_task" }
    ],
    "history": [],
    "error": null
  },
  "meta": {}
}
```

Ejemplo de error de acción (sin romper chat):

```json
{
  "data": {
    "success": true,
    "provider_available": true,
    "fallback_mode": false,
    "answer": "I cannot create a task with a due date in the past...",
    "actions": [
      {
        "tool_name": "create_task",
        "result": { "error": "400: Due date cannot be in the past", "tool": "create_task" }
      }
    ]
  }
}
```

## Tests

Backend:

```powershell
cd c:/Proyectos/Prueba_Projectus/backend
pipenv run pytest -q
```

Frontend build:

```powershell
cd c:/Proyectos/Prueba_Projectus/frontend
npm run build
```

## Troubleshooting

### Si aparece "modo degradado" pero DeepSeek tiene saldo

1. Asegúrate de que frontend apunte al puerto correcto:
   - frontend/.env debe tener VITE_API_BASE_URL=http://127.0.0.1:8010
2. Verifica que no haya múltiples backends activos en puertos distintos.
3. Haz hard refresh del navegador (Ctrl+F5).

### Limpiar procesos en Windows

```powershell
Get-Process -Name uvicorn,python,node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
```

### Validar puertos ocupados

```powershell
netstat -ano | Select-String ':8010'
netstat -ano | Select-String ':5174'
```

### Errores comunes

- AI_AUTH_ERROR: API key inválida
- AI_BILLING_ERROR: saldo/créditos insuficientes
- AI_TIMEOUT: timeout de provider
- AI_CONFIG_ERROR: variables incompletas o payload inválido

## Seguridad

1. No subas llaves reales ni cadenas de conexión en .env.example.
2. Si una key fue expuesta, rótala de inmediato.
3. Usa placeholders replace_me en archivos versionados.
