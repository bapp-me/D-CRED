$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m dcred.cli run-reject-capacity `
  --run-name reject_capacity_sanity `
  --lending-max-rows 10000 `
  --models lr `
  --bootstrap 0 `
  --n-jobs 1

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
