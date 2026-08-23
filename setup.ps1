# Script para configurar el entorno de desarrollo en Windows

$ErrorActionPreference = "Stop"

Write-Host "=== Iniciando configuración del entorno para FastAPI Backend ===" -ForegroundColor Cyan

# Verificar si Python está instalado
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python no está instalado o no se encuentra en el PATH de Windows. Por favor, instálalo antes de continuar."
    exit 1
}

# 2. Crear entorno virtual si no existe
if (!(Test-Path ".venv")) {
    Write-Host "`n[1/4] Creando entorno virtual (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Entorno virtual creado." -ForegroundColor Green
} else {
    Write-Host "`n[1/4] El entorno virtual (.venv) ya existe. Saltando paso." -ForegroundColor Gray
}

# 3. Actualizar pip e instalar dependencias
Write-Host "`n[2/4] Actualizando pip e instalando dependencias..." -ForegroundColor Yellow
& .venv\Scripts\python.exe -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    & .venv\Scripts\pip.exe install -r requirements.txt
    Write-Host "Dependencias instaladas correctamente." -ForegroundColor Green
} else {
    Write-Warning "No se encontró el archivo requirements.txt. Instalando paquetes básicos..."
    & .venv\Scripts\pip.exe install fastapi uvicorn supabase python-dotenv
}

# 3b. JobSpy (HU-57) se instala aparte, con --no-deps.
# El paquete declara numpy==1.26.3, que no publica wheels para Python 3.13+
# y hace que pip intente compilar numpy desde fuente (y falle si no hay
# compilador C). Sus dependencias reales ya vienen en requirements.txt.
Write-Host "`nInstalando JobSpy (recolector de ofertas laborales)..." -ForegroundColor Yellow
& .venv\Scripts\pip.exe install python-jobspy==1.1.82 --no-deps
Write-Host "JobSpy instalado." -ForegroundColor Green

# 4. Crear .env.local si no existe
Write-Host "`n[3/4] Verificando archivo de variables de entorno..." -ForegroundColor Yellow
if (!(Test-Path ".env.local")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.local"
        Write-Host "Se ha creado el archivo .env.local basado en .env.example." -ForegroundColor Green
        Write-Host "Por favor, recuerda abrir .env.local y configurar tus credenciales de Supabase." -ForegroundColor Cyan
    } else {
        # Crear un .env.local vacío básico si tampoco hay .env.example
        New-Item -Path "." -Name ".env.local" -ItemType "file" -Value "SUPABASE_URL=`nSUPABASE_ANON_KEY=`nFRONTEND_URL=http://localhost:3000`n" > $null
        Write-Host "Se creó un archivo .env.local vacío. Llena tus datos de Supabase allí." -ForegroundColor Yellow
    }
} else {
    Write-Host "El archivo .env.local ya existe." -ForegroundColor Gray
}

# 5. Crear archivo vacío __init__.py en carpetas necesarias si no existen
Write-Host "`n[4/4] Verificando estructura de paquetes Python..." -ForegroundColor Yellow
$folders = @("api", "core", "database", "schemas", "services")
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        $initFile = Join-Path $folder "__init__.py"
        if (!(Test-Path $initFile)) {
            New-Item -Path $initFile -ItemType "file" > $null
            Write-Host "Creado __init__.py en la carpeta '$folder'." -ForegroundColor Gray
        }
    }
}

Write-Host "`n=== ¡Configuración completada! ===" -ForegroundColor Green
Write-Host "Usa '.\run.ps1' para iniciar tu servidor." -ForegroundColor Cyan