from __future__ import annotations

import argparse
from pathlib import Path

from .config import OUTPUT_DIR, RAW_DATA_DIR
from .data import ensure_german_credit, ensure_lending_club, ensure_uci_default
from .experiment import RunConfig, run_all, run_lending, run_reduced, run_reject_option_capacity
from .utils import ensure_dir, now_stamp, write_json


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dcred",
        description="D-CRED deployment-oriented credit-risk experiments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download-data", help="Download all raw datasets.")
    _add_data_args(download)

    audit = subparsers.add_parser("audit", help="Download data and write dataset audits.")
    _add_common_args(audit)
    audit.add_argument("--lending-max-rows", type=int, default=None)

    lending = subparsers.add_parser("run-lending", help="Run Lending Club LTF experiments.")
    _add_common_args(lending)
    _add_model_args(lending)
    lending.add_argument("--lending-max-rows", type=int, default=None)

    reduced = subparsers.add_parser("run-reduced", help="Run UCI/German reduced protocol.")
    _add_common_args(reduced)
    _add_model_args(reduced)
    reduced.add_argument("--reduced-seeds", nargs="+", type=int, default=[42, 43, 44])

    all_parser = subparsers.add_parser("run-all", help="Run Lending + reduced protocols.")
    _add_common_args(all_parser)
    _add_model_args(all_parser)
    all_parser.add_argument("--lending-max-rows", type=int, default=None)
    all_parser.add_argument("--reduced-seeds", nargs="+", type=int, default=[42, 43, 44])

    reject_capacity = subparsers.add_parser(
        "run-reject-capacity",
        help="Run the chronological role-split reject-option and capacity-aware protocol.",
    )
    _add_common_args(reject_capacity)
    _add_model_args(reject_capacity)
    reject_capacity.add_argument("--lending-max-rows", type=int, default=None)
    reject_capacity.add_argument("--primary-cost-ratio", type=float, default=5.0)
    reject_capacity.add_argument("--primary-review-cost", type=float, default=0.10)
    reject_capacity.add_argument("--primary-human-residual-rho", type=float, default=0.10)

    args = parser.parse_args()

    if args.command == "download-data":
        raw_dir = Path(args.raw_dir)
        ensure_lending_club(raw_dir)
        ensure_uci_default(raw_dir)
        ensure_german_credit(raw_dir)
        return

    output_dir = _resolve_output_dir(Path(args.output_dir), args.run_name)
    config = RunConfig(
        output_dir=output_dir,
        raw_dir=Path(args.raw_dir),
        seed=args.seed,
        models=getattr(args, "models", ["lr", "rf", "xgb"]),
        n_jobs=args.n_jobs,
        rf_estimators=getattr(args, "rf_estimators", 300),
        xgb_estimators=getattr(args, "xgb_estimators", 500),
        use_gpu_xgb=getattr(args, "use_gpu_xgb", False),
        include_text=args.include_text,
        text_max_features=args.text_max_features,
        bootstrap=args.bootstrap,
        lending_max_rows=getattr(args, "lending_max_rows", None),
        tree_max_train_rows=getattr(args, "tree_max_train_rows", None),
        reduced_seeds=tuple(getattr(args, "reduced_seeds", [42, 43, 44])),
    )
    write_json(
        output_dir / "run_config.json",
        {
            "command": args.command,
            "config": {
                "output_dir": str(config.output_dir),
                "raw_dir": str(config.raw_dir),
                "seed": config.seed,
                "models": config.models,
                "n_jobs": config.n_jobs,
                "rf_estimators": config.rf_estimators,
                "xgb_estimators": config.xgb_estimators,
                "use_gpu_xgb": config.use_gpu_xgb,
                "include_text": config.include_text,
                "text_max_features": config.text_max_features,
                "bootstrap": config.bootstrap,
                "lending_max_rows": config.lending_max_rows,
                "tree_max_train_rows": config.tree_max_train_rows,
                "reduced_seeds": list(config.reduced_seeds),
            },
        },
    )

    if args.command == "audit":
        audit_config = RunConfig(**{**config.__dict__, "models": ["lr"], "bootstrap": 0})
        run_lending(audit_config)
    elif args.command == "run-lending":
        run_lending(config)
    elif args.command == "run-reduced":
        run_reduced(config)
    elif args.command == "run-all":
        run_all(config)
    elif args.command == "run-reject-capacity":
        run_reject_option_capacity(
            config,
            primary_cost_ratio=args.primary_cost_ratio,
            primary_review_cost=args.primary_review_cost,
            primary_human_residual_rho=args.primary_human_residual_rho,
        )
    else:
        raise ValueError(args.command)


def _add_data_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--raw-dir", default=str(RAW_DATA_DIR), help="Raw data directory.")


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    _add_data_args(parser)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Base output directory.")
    parser.add_argument("--run-name", default=None, help="Run subdirectory name.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--text-max-features", type=int, default=2048)
    parser.add_argument("--bootstrap", type=int, default=200)


def _add_model_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--models", nargs="+", default=["lr", "rf", "xgb"])
    parser.add_argument("--rf-estimators", type=int, default=300)
    parser.add_argument("--xgb-estimators", type=int, default=500)
    parser.add_argument("--use-gpu-xgb", action="store_true")
    parser.add_argument(
        "--tree-max-train-rows",
        type=int,
        default=None,
        help="Optional stratified training cap for memory-heavy tree baselines; evaluation still uses the full validation/test split.",
    )


def _resolve_output_dir(base: Path, run_name: str | None) -> Path:
    if run_name is None:
        run_name = now_stamp()
    path = base / run_name
    ensure_dir(path)
    return path


if __name__ == "__main__":
    main()
