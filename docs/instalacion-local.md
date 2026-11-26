# Instalación local del servidor tony-estandares

El ejercicio del Enablement no usa el modo local: usa solo el modo remoto, que se explica en [flujo-render.md](flujo-render.md). Esta guía conserva las instrucciones del modo local (stdio), donde Kiro arranca el servidor como proceso en tu máquina, para usarlas fuera del ejercicio. Por ejemplo, para probar reglas nuevas antes de publicarlas o para trabajar sin internet.

Se probó con la versión 2.3.0 del SDK `mcp`. El modo local también funciona con la serie 1.x (`requirements.txt` declara `mcp[cli]>=1.10,<3`). El modo remoto requiere el SDK 2.x.

## Instalación local en Windows (recomendada)

El proyecto funciona en cualquier carpeta, incluso con espacios o tildes en la ruta (por ejemplo `C:/Users/<tú>/Proyectos - Kiro/Sesión 5/tony-mcp`). `server.py` busca `reglas/` junto a sí mismo, no en el directorio de trabajo. Lo único que depende de la ruta es el `mcp.json` de Kiro, y el instalador lo escribe por ti.

Requisitos: Python 3.10 o superior ([python.org](https://www.python.org/downloads/), marca *Add python.exe to PATH*) y Git, o la descarga del ZIP del repositorio.

Se clona tu Fork, no el Repositorio original: reemplaza `<tu-usuario>` por tu usuario de GitHub.

```powershell
git clone https://github.com/<tu-usuario>/MCP-Tony.git tony-mcp
cd tony-mcp
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

El instalador:

1. Busca Python 3.10 o superior (`py -3`, `python` o `python3`).
2. Crea el entorno virtual `.venv` en la carpeta del proyecto, si no existe, e instala las dependencias.
3. Comprueba que el servidor registra sus tres herramientas.
4. Agrega o actualiza la entrada `tony-estandares` en `~/.kiro/settings/mcp.json` con las rutas de esa carpeta. Antes guarda un respaldo `mcp.json.bak-<fecha>` y no toca las demás entradas.

Después abre el panel de MCP en Kiro y reconecta `tony-estandares` si no aparece solo.

`-ExecutionPolicy Bypass` solo aplica a esa ejecución y evita el bloqueo de scripts de Windows sin cambiar tu configuración.

Opciones:

| Opción | Uso |
|---|---|
| `-SoloMostrar` | No modifica ningún archivo; imprime el bloque JSON para pegarlo a mano. |
| `-RutaConfig <ruta>` | Escribe en otro `mcp.json`, por ejemplo el de un workspace: `.kiro\settings\mcp.json`. |
| `-Nombre <nombre>` | Usa otro nombre de servidor, por ejemplo para tener dos copias. |

**Si mueves o renombras la carpeta**, vuelve a ejecutar `instalar.ps1` desde la nueva ubicación. Un `.venv` movido puede conservar rutas de la ubicación anterior, así que bórralo antes (`Remove-Item -Recurse .venv`) para que el instalador lo cree de nuevo.

**Ruta estándar para equipos (opcional).** Si todos instalan en la misma ruta, por ejemplo `C:/tools/tony-mcp`, las instrucciones y capturas son idénticas en todas las máquinas y es más fácil dar soporte. No es obligatorio: el instalador funciona en cualquier ruta.

## Instalación manual

### Windows

Desde PowerShell, en la carpeta del proyecto. El entorno virtual no se activa: los comandos invocan directamente el Python del entorno.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para obtener las dos rutas que pide Kiro, con barras `/`:

```powershell
(Resolve-Path .\.venv\Scripts\python.exe).Path -replace '\\','/'
(Resolve-Path .\server.py).Path -replace '\\','/'
```

### macOS y Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
echo "$PWD/.venv/bin/python"
echo "$PWD/server.py"
```

### Conexión con Kiro

Agrega el servidor en `~/.kiro/settings/mcp.json` (todos tus proyectos) o en `.kiro/settings/mcp.json` (solo un workspace). Reemplaza las rutas por las que obtuviste arriba. Si el archivo ya tiene otros servidores, agrega `tony-estandares` dentro del `mcpServers` existente.

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

- `command` apunta al Python del entorno virtual, así que Kiro usa las dependencias instaladas sin activar nada. En macOS y Linux termina en `.venv/bin/python`.
- No hacen falta comillas extra por los espacios o tildes: Kiro pasa `command` y `args` al proceso como valores separados.
- Guarda el archivo en UTF-8. El editor de Kiro lo hace solo; un editor antiguo podría corromper las tildes de la ruta.

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

## Probar el modo HTTP en local

```powershell
$env:MCP_TRANSPORT = "streamable-http"; $env:MCP_TOKEN = "token-de-prueba"; $env:PORT = "8000"
.\.venv\Scripts\python.exe server.py
```

Este comando sí queda corriendo; detenlo con Ctrl+C. Para volver al modo stdio en esa terminal, borra la variable con `Remove-Item Env:MCP_TRANSPORT`.

## Problemas frecuentes

| Síntoma | Causa probable y solución |
|---|---|
| `instalar.ps1` no se puede cargar porque la ejecución de scripts está deshabilitada | Ejecútalo con `powershell -ExecutionPolicy Bypass -File .\instalar.ps1`, como se indica arriba. |
| "no encontré Python 3.10 o superior" | Instala Python desde python.org y marca *Add python.exe to PATH*. El alias `python` que solo abre la Microsoft Store no es una instalación de Python. |
| `tony-estandares` no aparece en el panel de MCP | Reconéctalo desde el panel y revisa la pestaña Output. Confirma que `command` apunta a un `python.exe` que existe. |
| Funcionaba y dejó de hacerlo tras mover la carpeta | Borra `.venv` y vuelve a ejecutar `instalar.ps1` desde la nueva ubicación. |
