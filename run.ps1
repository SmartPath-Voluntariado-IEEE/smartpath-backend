# Script para arrancar el servidor FastAPI de manera local

Write-Host "=== Iniciando servidor FastAPI ===" -ForegroundColor Cyan

# 1. Comprobar que el entorno virtual existe
if (!(Test-Path ".venv")) {
    Write-Error "No se encontró la carpeta del entorno virtual (.venv). Por favor, ejecuta primero '.\setup.ps1'"
    exit 1
}

# 2. Advertir si falta configurar las variables
if (Test-Path ".env.local") {
    $envContent = Get-Content ".env.local" -Raw
    if ($envContent -match "SUPABASE_URL=\s*`r?`$" -or $envContent -match "SUPABASE_ANON_KEY=\s*`r?`$") {
        Write-Warning "El archivo .env.local parece no tener las credenciales de Supabase configuradas. El servidor podría fallar al iniciar."
    }
} else {
    Write-Warning "No se encontró el archivo .env.local. Creando uno básico..."
    New-Item -Path "." -Name ".env.local" -ItemType "file" -Value "SUPABASE_URL=`nSUPABASE_ANON_KEY=`nFRONTEND_URL=http://localhost:3000`n" > $null
}

# 3. Lanzar servidor
Write-Host "Levantando Uvicorn..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" -m uvicorn main:app --reload