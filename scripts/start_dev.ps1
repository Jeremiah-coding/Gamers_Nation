param(
	[switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExe)) {
	throw "Python virtualenv executable not found at $pythonExe"
}

if ($InstallDeps) {
	Write-Host "Installing Python dependencies..."
	& $pythonExe -m pip install -r requirements.txt
	if ($LASTEXITCODE -ne 0) {
		throw "Dependency installation failed."
	}
}

Write-Host "Preparing PostgreSQL and environment variables..."
. (Join-Path $PSScriptRoot "setup_postgres.ps1")

Write-Host "Starting Flask development server..."
& $pythonExe server.py
