$ErrorActionPreference = "Stop"

Write-Host "This copies the local Docker PostgreSQL database to an EMPTY Render database."
Write-Host "Use the Render External Database URL. The URL is read as a secure prompt and is not printed."
$secureTargetUrl = Read-Host "Render External Database URL" -AsSecureString
$targetUrl = [System.Net.NetworkCredential]::new("", $secureTargetUrl).Password
if ([string]::IsNullOrWhiteSpace($targetUrl)) {
    throw "A Render database URL is required."
}

try {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop must be running."
    }

    $migrationScript = @'
set -eu
target_has_users=$(psql "$TARGET_DATABASE_URL" -v ON_ERROR_STOP=1 -Atc "SELECT to_regclass('public.users') IS NOT NULL")
if [ "$target_has_users" = "t" ]; then
    echo "Refusing to overwrite a target database that already has a users table." >&2
    exit 2
fi
pg_dump "$SOURCE_DATABASE_URL" --no-owner --no-acl --format=custom --file=/tmp/gamers_nation.dump
pg_restore --no-owner --no-acl --exit-on-error --dbname="$TARGET_DATABASE_URL" /tmp/gamers_nation.dump
echo "Database migration completed."
'@
    $migrationScript = $migrationScript -replace "`r`n", "`n" -replace "`r", "`n"

    $sourceUrl = "postgresql://postgres:postgres@host.docker.internal:15432/videogames_schema"
    $dockerOutput = $migrationScript | & docker run --rm -i `
        -e "SOURCE_DATABASE_URL=$sourceUrl" `
        -e "TARGET_DATABASE_URL=$targetUrl" `
        postgres:16-alpine sh -s 2>&1 | Out-String
    $dockerExitCode = $LASTEXITCODE
    $safeOutput = $dockerOutput.Replace($targetUrl, "[REDACTED DATABASE URL]")
    $safeOutput = $safeOutput.Replace($sourceUrl, "[LOCAL DATABASE URL]")
    $safeOutput = $safeOutput -replace 'postgres(?:ql)?://[^:\s]+:[^@\s]+@', 'postgresql://[REDACTED]@'
    if ($safeOutput.Trim()) {
        Write-Host $safeOutput.TrimEnd()
    }
    if ($dockerExitCode -ne 0) {
        throw "Database migration failed (docker exit $dockerExitCode). The local source was not modified, but the Render target might be partially restored. Inspect the sanitized error above before retrying."
    }
}
finally {
    $targetUrl = $null
    $secureTargetUrl.Dispose()
}
