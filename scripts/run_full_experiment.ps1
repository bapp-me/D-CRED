$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m dcred.cli run-all `
  --run-name full `
  --models lr rf xgb `
  --rf-estimators 100 `
  --xgb-estimators 300 `
  --use-gpu-xgb `
  --bootstrap 200 `
  --tree-max-train-rows 50000 `
  --n-jobs 1

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
