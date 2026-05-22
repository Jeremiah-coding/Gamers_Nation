param(
    [string]$PgUser = "postgres",
    [string]$PgPassword = "postgres",
    [string]$PgDatabase = "videogames_schema",
    [string]$PgHost = "localhost",
    [string]$PgPort = "15432"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking Docker availability..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is not installed or not in PATH. Install Docker Desktop first."
}

Write-Host "Starting PostgreSQL via Docker Compose..."
docker compose up -d postgres | Out-Host

Write-Host "Waiting for PostgreSQL health check..."
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    $attempt++
    $status = docker inspect --format='{{.State.Health.Status}}' gamers_nation_postgres 2>$null
    if ($status -eq "healthy") {
        break
    }
    Start-Sleep -Seconds 2
}

if ($status -ne "healthy") {
    throw "PostgreSQL container did not become healthy in time."
}

Write-Host "Ensuring database '$PgDatabase' exists..."
$checkDb = docker exec gamers_nation_postgres psql -U $PgUser -tAc "SELECT 1 FROM pg_database WHERE datname='$PgDatabase';"
if ($checkDb.Trim() -ne "1") {
    docker exec gamers_nation_postgres psql -U $PgUser -c "CREATE DATABASE $PgDatabase;" | Out-Host
}

Write-Host "Configuring environment variables for this PowerShell session..."
$env:DB_BACKEND = "postgres"
$env:PGHOST = $PgHost
$env:PGPORT = $PgPort
$env:PGUSER = $PgUser
$env:PGPASSWORD = $PgPassword
$env:PGDATABASE = $PgDatabase
$env:DATABASE_URL = "postgresql://$PgUser`:$PgPassword@$PgHost`:$PgPort/$PgDatabase"

Write-Host "Validating application DB connection..."
$pythonExe = "c:/Users/jerem/Gamers_Nation/.venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python virtualenv executable not found at $pythonExe"
}

& $pythonExe -c "from flask_app.config.mysqlconnection import connectToMySQL; print(connectToMySQL('videogames_schema').query_db('SELECT 1 as ok;'))"
if ($LASTEXITCODE -ne 0) {
    throw "Application DB validation failed."
}

Write-Host "PostgreSQL setup complete."
Write-Host "Environment variables have been set for this PowerShell session."
Write-Host "DATABASE_URL=$($env:DATABASE_URL)"
Write-Host "Run: $pythonExe server.py"
