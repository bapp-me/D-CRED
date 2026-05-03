from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass(frozen=True)
class ModelSpec:
    name: str
    estimator: object


def build_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
    text_feature: str | None,
    text_max_features: int,
) -> ColumnTransformer:
    transformers = []
    if numeric_features:
        transformers.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )
    if categorical_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                min_frequency=10,
                                sparse_output=True,
                            ),
                        ),
                    ]
                ),
                categorical_features,
            )
        )
    if text_feature:
        transformers.append(
            (
                "text",
                TfidfVectorizer(
                    max_features=text_max_features,
                    ngram_range=(1, 2),
                    min_df=5,
                    strip_accents="unicode",
                ),
                text_feature,
            )
        )
    return ColumnTransformer(transformers, sparse_threshold=0.3)


def build_models(
    names: Iterable[str],
    seed: int,
    n_jobs: int,
    rf_estimators: int,
    xgb_estimators: int,
    use_gpu_xgb: bool,
) -> list[ModelSpec]:
    specs: list[ModelSpec] = []
    for name in names:
        key = name.lower()
        if key in {"lr", "logistic", "logistic_regression"}:
            specs.append(
                ModelSpec(
                    "lr",
                    SGDClassifier(
                        loss="log_loss",
                        penalty="l2",
                        alpha=1e-4,
                        max_iter=1000,
                        tol=1e-4,
                        average=True,
                        early_stopping=True,
                        validation_fraction=0.1,
                        n_iter_no_change=5,
                        class_weight="balanced",
                        random_state=seed,
                    ),
                )
            )
        elif key in {"rf", "random_forest"}:
            specs.append(
                ModelSpec(
                    "rf",
                    _build_lightgbm_rf(seed, n_jobs, rf_estimators),
                )
            )
        elif key in {"xgb", "xgboost"}:
            specs.append(
                ModelSpec(
                    "xgb",
                    _build_xgb(seed, n_jobs, xgb_estimators, use_gpu_xgb),
                )
            )
        elif key in {"lgbm", "lightgbm"}:
            specs.append(ModelSpec("lgbm", _build_lgbm(seed, n_jobs)))
        else:
            raise ValueError(f"Unknown model name: {name}")
    return specs


def _build_xgb(seed: int, n_jobs: int, n_estimators: int, use_gpu: bool):
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("xgboost is required for --models xgb") from exc

    kwargs = {
        "n_estimators": n_estimators,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": seed,
        "n_jobs": n_jobs,
        "tree_method": "hist",
    }
    if use_gpu:
        kwargs["device"] = "cuda"
    return XGBClassifier(**kwargs)


def _build_lightgbm_rf(seed: int, n_jobs: int, n_estimators: int):
    try:
        from lightgbm import LGBMClassifier
    except ImportError as exc:
        raise RuntimeError("lightgbm is required for the rf baseline on this project") from exc
    return LGBMClassifier(
        boosting_type="rf",
        n_estimators=n_estimators,
        learning_rate=1.0,
        num_leaves=63,
        max_depth=12,
        min_child_samples=50,
        bagging_freq=1,
        bagging_fraction=0.8,
        feature_fraction=0.8,
        class_weight="balanced",
        random_state=seed,
        n_jobs=n_jobs,
        verbose=-1,
    )


def _build_lgbm(seed: int, n_jobs: int):
    try:
        from lightgbm import LGBMClassifier
    except ImportError as exc:
        raise RuntimeError("lightgbm is required for --models lgbm") from exc
    return LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        subsample=0.9,
        colsample_bytree=0.9,
        class_weight="balanced",
        random_state=seed,
        n_jobs=n_jobs,
        verbose=-1,
    )


def make_pipeline(preprocessor: ColumnTransformer, estimator: object) -> Pipeline:
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])


def fit_with_gpu_fallback(
    pipeline: Pipeline,
    x_train: pd.DataFrame,
    y_train: np.ndarray,
) -> Pipeline:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipeline.fit(x_train, y_train)
        return pipeline
    except Exception as exc:
        if isinstance(exc, PermissionError) or "permissionerror" in str(exc).lower():
            return _fit_single_job_fallback(pipeline, x_train, y_train, exc)
        message = str(exc).lower()
        if "cuda" not in message and "gpu" not in message and "xgboost" not in message:
            raise
        model = pipeline.named_steps["model"]
        if model.__class__.__name__ != "XGBClassifier":
            raise
        params = model.get_params()
        params.pop("device", None)
        params["tree_method"] = "hist"
        from xgboost import XGBClassifier

        fallback = Pipeline(
            [
                ("preprocess", pipeline.named_steps["preprocess"]),
                ("model", XGBClassifier(**params)),
            ]
        )
        warnings.warn(
            f"XGBoost GPU training failed; retrained on CPU. Original error: {exc}",
            RuntimeWarning,
        )
        fallback.fit(x_train, y_train)
        return fallback


def _fit_single_job_fallback(
    pipeline: Pipeline,
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    original_error: Exception,
) -> Pipeline:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "get_params"):
        raise original_error
    params = model.get_params()
    if "n_jobs" not in params:
        raise original_error
    params["n_jobs"] = 1
    fallback_model = model.__class__(**params)
    fallback = Pipeline(
        [
            ("preprocess", pipeline.named_steps["preprocess"]),
            ("model", fallback_model),
        ]
    )
    warnings.warn(
        "Parallel fitting failed under the local Windows sandbox; "
        "retrying this estimator with n_jobs=1.",
        RuntimeWarning,
    )
    fallback.fit(x_train, y_train)
    return fallback


def predict_default_proba(pipeline: Pipeline, x_frame: pd.DataFrame) -> np.ndarray:
    if hasattr(pipeline, "predict_proba"):
        return pipeline.predict_proba(x_frame)[:, 1]
    scores = pipeline.decision_function(x_frame)
    return 1.0 / (1.0 + np.exp(-scores))
