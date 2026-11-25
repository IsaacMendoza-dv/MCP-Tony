<#
.SYNOPSIS
Instala tony-estandares en la carpeta de este script y lo registra en Kiro.

.DESCRIPTION
Funciona desde cualquier ruta, incluso con espacios o tildes. Crea el entorno
virtual .venv, instala las dependencias, comprueba que el servidor registra sus
tres herramientas y agrega (o actualiza) la entrada en el mcp.json de usuario
de Kiro con las rutas de esta carpeta. Si mueves la carpeta, vuelve a
ejecutarlo para actualizar las rutas.

Antes de modificar el mcp.json guarda una copia de respaldo junto a él. Las
demás entradas de mcpServers no se tocan.

.PARAMETER RutaConfig
mcp.json que se modifica. Por defecto, el de usuario: ~/.kiro/settings/mcp.json.

.PARAMETER Nombre
Nombre del servidor dentro de mcpServers. Por defecto, tony-estandares.

.PARAMETER SoloMostrar
No modifica ningún mcp.json; solo imprime el bloque de configuración.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\instalar.ps1

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\instalar.ps1 -SoloMostrar
#>
param(
    [string]$RutaConfig = (Join-Path $HOME ".kiro\settings\mcp.json"),
    [string]$Nombre = "tony-estandares",
    [switch]$SoloMostrar
)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$herramientas = @("listar_reglas", "obtener_regla", "buscar_reglas")

function Paso([string]$texto) { Write-Host "==> $texto" -ForegroundColor Cyan }

function Fallar([string]$texto) {
    Write-Host "Error: $texto" -ForegroundColor Red
    exit 1
}

# Ejecuta un programa externo sin que sus avisos en stderr detengan el script.
function Ejecutar([string]$programa, [string[]]$argumentos) {
    $anterior = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $salida = & $programa @argumentos 2>&1
        $codigo = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $anterior
    }
    return [pscustomobject]@{ Codigo = $codigo; Salida = ($salida | Out-String).Trim() }
}

function RutaJson([string]$ruta) { return $ruta -replace '\\', '/' }

# 1. Python 3.10 o superior (el SDK mcp lo exige).
Paso "Buscando Python 3.10 o superior"
$candidatos = @(
    @{ Exe = "py"; Args = @("-3") },
    @{ Exe = "python"; Args = @() },
    @{ Exe = "python3"; Args = @() }
)
$python = $null
foreach ($candidato in $candidatos) {
    if (-not (Get-Command $candidato.Exe -ErrorAction SilentlyContinue)) { continue }
    $prueba = Ejecutar $candidato.Exe ($candidato.Args + @("-c", "import sys; print(sys.version_info >= (3, 10))"))
    if ($prueba.Codigo -eq 0 -and $prueba.Salida -eq "True") { $python = $candidato; break }
}
if (-not $python) {
    Fallar "no encontré Python 3.10 o superior. Instálalo desde https://www.python.org/downloads/ y marca 'Add python.exe to PATH'."
}

# 2. Entorno virtual en la carpeta del proyecto.
$venvPython = Join-Path $raiz ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Paso "Usando el entorno virtual existente (.venv)"
} else {
    Paso "Creando el entorno virtual (.venv)"
    $r = Ejecutar $python.Exe ($python.Args + @("-m", "venv", (Join-Path $raiz ".venv")))
    if ($r.Codigo -ne 0) { Fallar "no se pudo crear el entorno virtual.`n$($r.Salida)" }
}

# 3. Dependencias.
Paso "Instalando dependencias"
$r = Ejecutar $venvPython @("-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", (Join-Path $raiz "requirements.txt"))
if ($r.Codigo -ne 0) { Fallar "pip no pudo instalar las dependencias.`n$($r.Salida)" }

# 4. Verificación sin arrancar el servidor.
Paso "Verificando el servidor"
Push-Location $raiz
try {
    $r = Ejecutar $venvPython @("-c", "import asyncio, server; print(','.join(t.name for t in asyncio.run(server.servidor.list_tools())))")
} finally {
    Pop-Location
}
$ultimaLinea = ($r.Salida -split "`r?`n")[-1].Trim()
if ($r.Codigo -ne 0 -or $ultimaLinea -ne ($herramientas -join ",")) {
    Fallar "el servidor no registró las tres herramientas.`n$($r.Salida)"
}

# 5. Entrada de Kiro con las rutas de esta carpeta.
$entrada = [ordered]@{
    command     = RutaJson $venvPython
    args        = @(RutaJson (Join-Path $raiz "server.py"))
    autoApprove = $herramientas
}

if ($SoloMostrar) {
    Paso "Bloque para mcpServers (no se modificó ningún archivo)"
    @{ mcpServers = @{ $Nombre = $entrada } } | ConvertTo-Json -Depth 5
    exit 0
}

Paso "Registrando '$Nombre' en $RutaConfig"
$utf8SinBom = New-Object System.Text.UTF8Encoding($false)
$config = $null
if (Test-Path $RutaConfig) {
    $texto = [System.IO.File]::ReadAllText($RutaConfig, [System.Text.Encoding]::UTF8)
    if ($texto.Trim()) {
        try {
            $config = $texto | ConvertFrom-Json
        } catch {
            Fallar "$RutaConfig no es JSON válido. Corrígelo o usa -SoloMostrar y pega el bloque a mano."
        }
    }
    $respaldo = "$RutaConfig.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $RutaConfig $respaldo
    Write-Host "    Respaldo: $respaldo"
} else {
    $carpeta = Split-Path $RutaConfig
    if (-not (Test-Path $carpeta)) { New-Item -ItemType Directory -Path $carpeta | Out-Null }
}
if ($null -eq $config) { $config = New-Object PSObject }
if ($config.PSObject.Properties.Name -notcontains "mcpServers") {
    $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue (New-Object PSObject)
}
$existia = $config.mcpServers.PSObject.Properties.Name -contains $Nombre
$config.mcpServers | Add-Member -NotePropertyName $Nombre -NotePropertyValue ([pscustomobject]$entrada) -Force
[System.IO.File]::WriteAllText($RutaConfig, ($config | ConvertTo-Json -Depth 20), $utf8SinBom)

if ($existia) { $accion = "actualizado" } else { $accion = "agregado" }
Write-Host ""
Write-Host "Listo: '$Nombre' $accion." -ForegroundColor Green
Write-Host "    command: $($entrada.command)"
Write-Host "    args:    $($entrada.args[0])"
Write-Host "En Kiro, abre el panel de MCP y reconecta '$Nombre' si no aparece solo."
