# tony-estandares: servidor MCP de estándares

Servidor MCP escrito en Python que expone, en modo de solo lectura, las reglas de estándares guardadas como archivos Markdown en la carpeta `reglas/`. Funciona de dos maneras:

- **Local (stdio):** cada persona lo instala y Kiro lo arranca como proceso. Es el modo por defecto.
- **Remoto (HTTP):** se despliega una vez, por ejemplo en Render, y el equipo se conecta por URL con un token. Ver [Uso remoto en Render](#uso-remoto-en-render).

Se probó con la versión 2.3.0 del SDK `mcp`. El modo local también funciona con la serie 1.x (`requirements.txt` declara `mcp[cli]>=1.10,<3`). El modo remoto requiere el SDK 2.x.

## Estructura

```
tony-mcp/
├── server.py
├── requirements.txt
├── README.md
└── reglas/
    ├── nombres-de-variables.md
    ├── estructura-de-commits.md
    └── manejo-de-errores.md
```

## Instalación

Desde PowerShell, en la carpeta `tony-mcp/`. El entorno virtual no se activa: los comandos invocan directamente el Python del entorno.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Conexión con Kiro

Agrega el servidor en `.kiro/settings/mcp.json`. Reemplaza `C:/ruta/a/tony-mcp` por la ruta real de tu proyecto:

```json
{
  "mcpServers": {
    "tony-estandares": {
      "command": "C:/ruta/a/tony-mcp/.venv/Scripts/python.exe",
      "args": ["C:/ruta/a/tony-mcp/server.py"],
      "autoApprove": ["listar_reglas", "obtener_regla", "buscar_reglas"]
    }
  }
}
```

`command` apunta al Python del entorno virtual, de modo que Kiro usa las dependencias instaladas sin activar nada.

## Herramientas

### `listar_reglas`

Lista los nombres de las reglas disponibles, en orden alfabético y sin la extensión `.md`. Solo incluye las reglas con nombre válido.

- Parámetros: ninguno.
- Ejemplo de uso: "Lista las reglas de estándares disponibles".
- Resultado: `["estructura-de-commits", "manejo-de-errores", "nombres-de-variables"]`

### `obtener_regla`

Devuelve el contenido completo de una regla.

- Parámetros: `nombre` (texto), nombre de la regla con o sin la extensión `.md`.
- Ejemplo de uso: "Dame la regla `manejo-de-errores`".
- Errores: nombre no válido, intento de acceder fuera de `reglas/` o regla inexistente.

### `buscar_reglas`

Busca un texto, sin distinguir mayúsculas de minúsculas, en el nombre y el contenido de las reglas.

- Parámetros: `texto` (texto), no puede estar vacío.
- Ejemplo de uso: "Busca en las reglas la palabra `commit`".
- Resultado: lista de `{"nombre": ..., "coincidencias": [{"linea": 3, "texto": "..."}]}`. Las líneas se numeran desde 1. Si solo coincide el nombre, `coincidencias` queda vacía.

## Agregar o modificar reglas

1. Crea o edita un archivo `.md` en la carpeta `reglas/`, con codificación UTF-8.
2. No necesitas reiniciar el servidor: cada llamada lee los archivos desde el disco.

Usa guiones y no espacios en el nombre del archivo (por ejemplo, `nombres-de-variables.md`). `listar_reglas` omite los archivos con nombre no válido, como los que tienen espacios. Los nombres pueden incluir letras con acento y `ñ`, números, guiones, guiones bajos y puntos, pero no pueden empezar con punto.

## Verificación sin arrancar el servidor

No ejecutes `python server.py` para comprobar la instalación, porque el servidor queda esperando mensajes por stdio y bloquea la terminal. Usa estos comandos desde `tony-mcp/`.

Registro de herramientas (debe imprimir `listar_reglas`, `obtener_regla` y `buscar_reglas`):

```powershell
.\.venv\Scripts\python.exe -c "import asyncio, server; print([t.name for t in asyncio.run(server.servidor.list_tools())])"
```

Manejo de errores (la última línea debe mencionar `ToolError` y el mensaje "La regla 'no-existe' no existe."):

```powershell
.\.venv\Scripts\python.exe -c "import asyncio, server; asyncio.run(server.servidor.call_tool('obtener_regla', {'nombre': 'no-existe'}))"
```

## Uso remoto en Render

Con la variable `MCP_TRANSPORT=streamable-http`, el servidor atiende por HTTP en `0.0.0.0` y en el puerto de la variable `PORT`. Rutas:

- `/mcp`: endpoint MCP (Streamable HTTP, sin estado). Exige la cabecera `Authorization: Bearer <MCP_TOKEN>`; sin ella responde 401.
- `/health`: responde `{"estado": "ok"}` sin token. Sirve para el chequeo de salud y no expone reglas.

Si `MCP_TOKEN` no está definido, el servidor no arranca en modo HTTP, para que nunca quede público sin protección.

### Crear el servicio

En Render, crea un **Web Service** conectado a este repositorio:

| Campo | Valor |
|---|---|
| Language | Python 3 |
| Branch | `main` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python server.py` |
| Instance Type | Free |

Variables de entorno:

| KEY | VALUE |
|---|---|
| `MCP_TRANSPORT` | `streamable-http` |
| `MCP_TOKEN` | un valor largo y aleatorio (botón **Generate**) |

No definas `PORT`: Render la asigna. El token vive solo en Render; no lo subas al repositorio.

Cada push a `main` redespliega el servicio, así que agregar o editar una regla en `reglas/` y hacer push basta para publicarla.

El plan Free se duerme tras un rato sin uso. La primera llamada después de eso puede tardar alrededor de un minuto mientras el servicio despierta.

### Conectar Kiro al servidor remoto

1. Define el token como variable de entorno de usuario en Windows (PowerShell) y reinicia Kiro para que la lea:

   ```powershell
   [Environment]::SetEnvironmentVariable("TONY_MCP_TOKEN", "<token>", "User")
   ```

2. Agrega el servidor en `~/.kiro/settings/mcp.json`. Reemplaza la URL por la de tu servicio:

   ```json
   {
     "mcpServers": {
       "tony-estandares-remoto": {
         "url": "https://mcp-tony.onrender.com/mcp",
         "headers": { "Authorization": "Bearer ${TONY_MCP_TOKEN}" },
         "autoApprove": ["listar_reglas", "obtener_regla", "buscar_reglas"]
       }
     }
   }
   ```

Si también tienes el servidor local, usa nombres distintos (`tony-estandares` y `tony-estandares-remoto`) o desactiva uno con `"disabled": true`.

### Comprobar el servicio

```powershell
Invoke-RestMethod https://mcp-tony.onrender.com/health
```

Debe responder `estado: ok`. Una petición a `/mcp` sin token debe responder 401.

### Probar el modo HTTP en local

```powershell
$env:MCP_TRANSPORT = "streamable-http"; $env:MCP_TOKEN = "token-de-prueba"; $env:PORT = "8000"
.\.venv\Scripts\python.exe server.py
```

Este comando sí queda corriendo; detenlo con Ctrl+C. Para volver al modo stdio en esa terminal, borra la variable con `Remove-Item Env:MCP_TRANSPORT`.
