"""Servidor MCP 'tony-estandares'.

Expone en modo de solo lectura las reglas de estándares almacenadas como
archivos Markdown en la carpeta 'reglas/', mediante el transporte stdio.
"""

import re
from pathlib import Path

# Requirements 1.1, 1.5, 1.6, 1.7: se usa MCPServer (SDK 2.x) y, si no está
# disponible, FastMCP (SDK 1.x), junto con el ToolError correspondiente.
try:
    from mcp.server.mcpserver import MCPServer as ServidorMCP
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:
    from mcp.server.fastmcp import FastMCP as ServidorMCP
    from mcp.server.fastmcp.exceptions import ToolError

# Requirement 7.4: la ruta es relativa a server.py, no al directorio de trabajo.
DIRECTORIO_REGLAS = Path(__file__).resolve().parent / "reglas"

# Requirement 1.4: la instancia se crea a nivel de módulo sin iniciar el transporte.
servidor = ServidorMCP("tony-estandares")


# Requirement 8.3: debe heredar de ToolError (no de Exception) para que el
# SDK 2.x devuelva el mensaje al cliente.
class ErrorHerramienta(ToolError):
    """Error de negocio con mensaje en español que el SDK devuelve al cliente."""


# Requirement 4.3: acepta letras con acento y 'ñ' (\w es Unicode en str).
PATRON_NOMBRE_VALIDO = re.compile(r"^[\w.-]+$")

# Requirement 7.2: letra de unidad al inicio, por ejemplo 'C:'.
PATRON_UNIDAD = re.compile(r"^[A-Za-z]:")


def validar_nombre_regla(nombre: str) -> str:
    r"""
    Valida y normaliza el parámetro 'nombre' recibido por una herramienta.

    Quita el sufijo '.md' si está presente. Si el nombre contiene separadores
    de ruta, '..', una letra de unidad o es una ruta absoluta, lanza
    ErrorHerramienta con el mensaje "No se permite acceder fuera del
    directorio de reglas." Si el nombre está vacío, empieza con punto o
    contiene cualquier carácter fuera de [\w.-] (se aceptan letras con acento
    y 'ñ'), lanza ErrorHerramienta con el mensaje "El nombre de la regla no
    es válido".

    Devuelve el nombre de la regla normalizado, sin extensión.
    """
    # Requirements 4.3, 4.4, 4.5, 4.7, 7.2, 7.5, 8.2
    if nombre.endswith(".md"):
        nombre = nombre[: -len(".md")]

    # Path traversal: se detecta antes que la validación general del patrón.
    if "/" in nombre or "\\" in nombre or ".." in nombre or PATRON_UNIDAD.match(nombre):
        raise ErrorHerramienta("No se permite acceder fuera del directorio de reglas.")

    if not nombre or nombre.startswith(".") or not PATRON_NOMBRE_VALIDO.match(nombre):
        raise ErrorHerramienta("El nombre de la regla no es válido")

    return nombre


def verificar_directorio_reglas() -> Path:
    """
    Comprueba que el directorio de reglas exista y sea un directorio.

    Devuelve la ruta del directorio de reglas. Lanza ErrorHerramienta si no
    existe.
    """
    # Requirement 8.1
    if not DIRECTORIO_REGLAS.is_dir():
        raise ErrorHerramienta("La carpeta 'reglas/' no se encontró.")
    return DIRECTORIO_REGLAS


def resolver_ruta_regla(nombre_regla: str) -> Path:
    """
    Construye la ruta absoluta del archivo .md de una regla.

    Verifica que la ruta resuelta, siguiendo los enlaces simbólicos, quede
    dentro del directorio de reglas. Lanza ErrorHerramienta si queda fuera.
    """
    # Requirements 7.1, 7.3
    base = DIRECTORIO_REGLAS.resolve()
    ruta = (base / f"{nombre_regla}.md").resolve()
    if not ruta.is_relative_to(base):
        raise ErrorHerramienta("No se permite acceder fuera del directorio de reglas.")
    return ruta


def listar_archivos_md() -> list[Path]:
    """
    Devuelve las rutas de los archivos .md del directorio de reglas.

    Omite los archivos con otra extensión y los que tienen un nombre no
    válido (por ejemplo, con espacios). El resultado va ordenado
    alfabéticamente por nombre de regla. Lee el directorio desde disco en
    cada llamada, sin caché.
    """
    # Requirements 3.1, 3.3, 3.4, 3.5, 6.1, 6.2
    directorio = verificar_directorio_reglas()
    archivos = []
    for ruta in directorio.iterdir():
        if ruta.suffix != ".md" or not ruta.is_file():
            continue
        try:
            if validar_nombre_regla(ruta.stem) != ruta.stem:
                continue
        except ErrorHerramienta:
            continue
        archivos.append(ruta)
    return sorted(archivos, key=lambda r: r.stem)


def leer_regla(ruta: Path) -> str:
    """
    Lee el archivo de una regla en UTF-8 directamente desde disco.

    Lanza ErrorHerramienta con el nombre de la regla y el problema de
    codificación si el contenido no se puede decodificar como UTF-8.
    """
    # Requirements 4.2, 5.5, 8.5
    try:
        return ruta.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ErrorHerramienta(
            f"La regla '{ruta.stem}' no se pudo leer como UTF-8: {error.reason}."
        ) from error


# Requirements 1.8, 1.9, 1.10, 1.11, 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 8.1
@servidor.tool()
def listar_reglas() -> list[str]:
    """
    Lista los nombres de las reglas de estándares disponibles.

    No recibe parámetros. Devuelve una lista de nombres de regla, sin la
    extensión .md y en orden alfabético ascendente. Omite los archivos con
    nombre no válido (por ejemplo, con espacios). Si no hay reglas, devuelve
    una lista vacía.
    """
    return [ruta.stem for ruta in listar_archivos_md()]


# Requirements 1.8, 1.9, 1.10, 1.11, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 7.1, 7.2, 7.3, 8.1, 8.5
@servidor.tool()
def obtener_regla(nombre: str) -> str:
    """
    Devuelve el contenido completo de una regla de estándares.

    Parámetros:
        nombre: nombre de la regla, con o sin la extensión .md.

    Devuelve el contenido de la regla como texto UTF-8. Si la regla no
    existe o el nombre no es válido, devuelve un error en español.
    """
    # Se valida antes de acceder al disco (Requirements 4.3, 4.4, 4.5, 7.2).
    nombre_regla = validar_nombre_regla(nombre)
    verificar_directorio_reglas()
    ruta = resolver_ruta_regla(nombre_regla)
    if not ruta.is_file():
        raise ErrorHerramienta(f"La regla '{nombre_regla}' no existe.")
    return leer_regla(ruta)


# Requirements 1.8, 1.9, 1.10, 1.11, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.2, 8.1
@servidor.tool()
def buscar_reglas(texto: str) -> list[dict]:
    """
    Busca un texto, sin distinguir mayúsculas de minúsculas, en el nombre y
    en el contenido de las reglas de estándares.

    Parámetros:
        texto: texto a buscar; no puede estar vacío ni contener solo espacios.

    Devuelve una lista de objetos con la forma
    {"nombre": str, "coincidencias": [{"linea": int, "texto": str}]}, donde
    "linea" empieza en 1. Si el texto solo coincide con el nombre de la
    regla, "coincidencias" es una lista vacía. Si nada coincide, devuelve una
    lista vacía.
    """
    # Requirement 5.6: se valida antes de acceder al disco.
    if not texto or not texto.strip():
        raise ErrorHerramienta("El texto de búsqueda es obligatorio.")

    # Requirement 8.1: listar_archivos_md verifica que exista el directorio.
    # Requirements 5.5, 6.2: se lee desde disco en cada llamada, sin caché.
    buscado = texto.casefold()
    resultados = []
    for ruta in listar_archivos_md():
        coincidencias = [
            {"linea": numero, "texto": linea}
            for numero, linea in enumerate(leer_regla(ruta).splitlines(), start=1)
            if buscado in linea.casefold()
        ]
        # Requirement 5.3: una coincidencia solo por nombre deja la lista vacía.
        if coincidencias or buscado in ruta.stem.casefold():
            resultados.append({"nombre": ruta.stem, "coincidencias": coincidencias})
    return resultados


# Requirements 1.2, 1.3: al ejecutarse como programa principal, atiende MCP por stdio.
if __name__ == "__main__":
    servidor.run()
