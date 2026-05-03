## Local Experiment Environment

- Backend: local Windows CUDA
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU
- Python: Anaconda Python 3.12
- Code dir: `D:\code\diss_codex\D-CRED`
- Data dir: `data/raw`
- Output dir: `outputs`
- wandb: false

Use local execution for `/run-experiment`. The core D-CRED experiments are tabular ML jobs; XGBoost can be launched with `--use-gpu-xgb` to use CUDA when the installed XGBoost build supports it.
