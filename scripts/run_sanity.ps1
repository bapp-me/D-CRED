$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m dcred.cli run-lending `
  --run-name sanity `
  --lending-max-rows 5000 `
  --models lr `
  --bootstrap 20 `
  --n-jobs 1

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
