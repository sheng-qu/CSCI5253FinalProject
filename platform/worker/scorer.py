"""Inference-time scoring.

Loads the Phase 6 artifact (model + graph state + preprocessing metadata)
"""

from __future__ import annotations

import math
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb


class Scorer:
    def __init__(self, artifact_path: str):
        self.art = joblib.load(artifact_path)
        self.model: xgb.XGBClassifier = self.art["model"]
        self._explainer = shap.TreeExplainer(self.model)
        self._feature_order = self.art["feature_order"]

    # public entry point
    def score(self, payload: dict, db_conn=None) -> dict[str, Any]:
        """Score a single raw transaction.
        """
        row = dict(payload)
        row["uid"] = self._build_uid(row)
        row.update(self._attach_graph_features(row, db_conn=db_conn))
        X = self._preprocess(row)
        proba = float(self.model.predict_proba(X)[:, 1][0])
        top = self._shap_top_signals(X, k=5)
        return {"fraud_proba": proba, "top_signals": top}

    # uid construction
    def _build_uid(self, row: dict) -> str:
        spec = self.art["uid_spec"]
        day = int((row.get("TransactionDT") or 0) // 86400)
        d1 = row.get("D1")
        if d1 is None or (isinstance(d1, float) and math.isnan(d1)):
            d1 = spec["derive_card_age_day"]["missing_D1_sentinel"]
        card_age_day = day - int(d1)
        parts = {f: self._str(row.get(f)) for f in spec["fields"]}
        parts["card_age_day"] = str(card_age_day)
        return spec["template"].format(**parts)

    # graph feature lookup 
    VELOCITY_WINDOWS = {"1h": 3600, "24h": 86400, "7d": 604800}

    def _attach_graph_features(self, row: dict, db_conn=None) -> dict:
        gs = self.art["graph_state"]
        out: dict[str, Any] = {}

        # neighbor fraud rate — fall back to global rate for unseen entities
        for e, table in gs["nbr_fraud_rate"].items():
            out[f"{e}__nbr_fraud_rate"] = table.get(
                self._keyable(row.get(e)), gs["global_rate"]
            )

        # degree — fall back to 1 (only itself)
        for col, table in gs["degree"].items():
            entity_col = col.split("__")[0]
            out[col] = table.get(self._keyable(row.get(entity_col)), 1)

        # amount aggregates
        amt = float(row.get("TransactionAmt") or 0.0)
        for e, table in gs["amt_stats"].items():
            mean, std = table.get(self._keyable(row.get(e)), (amt, 0.0))
            out[f"{e}__amt_mean"] = mean
            out[f"{e}__amt_std"] = std
            out[f"{e}__amt_ratio"] = amt / (mean + 1e-6)

        # velocity — count events for (entity, value) within each window.
        now_dt = int(row.get("TransactionDT") or 0)
        entity_values = {"uid": row.get("uid"), "card1": row.get("card1")}
        for e, val in entity_values.items():
            for label, window_sec in self.VELOCITY_WINDOWS.items():
                key = f"{e}__vel_{label}"
                if db_conn is None or val is None:
                    out[key] = 0
                    continue
                with db_conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT count(*) FROM velocity_events
                         WHERE entity_type=%s
                           AND entity_value=%s
                           AND transaction_dt BETWEEN %s AND %s
                        """,
                        (e, str(val), now_dt - window_sec, now_dt),
                    )
                    out[key] = int(cur.fetchone()[0])

        return out

    # preprocessing 
    def _preprocess(self, row: dict) -> np.ndarray:
        pp = self.art["preprocessing"]
        # missingness indicators
        for c in pp["missing_indicator_cols"]:
            v = row.get(c)
            row[f"{c}_missing"] = int(v is None or (isinstance(v, float) and math.isnan(v)))
        # label-encode known categoricals
        for c, mapping in pp["label_encoders"].items():
            v = row.get(c)
            v = "NA" if (v is None or (isinstance(v, float) and math.isnan(v))) else str(v)
            row[c] = mapping.get(v, 0)  # unseen → 0 bucket
        # assemble vector in the exact order the model was trained on
        vec = [self._numeric(row.get(f)) for f in self._feature_order]
        return np.array(vec, dtype=float).reshape(1, -1)

    # SHAP explanation
    def _shap_top_signals(self, X: np.ndarray, k: int = 5) -> list[dict[str, Any]]:
        sv = self._explainer.shap_values(X)[0]
        order = np.argsort(-np.abs(sv))[:k]
        return [
            {
                "feature": self._feature_order[i],
                "value": float(X[0, i]) if not math.isnan(X[0, i]) else None,
                "shap_contribution": float(sv[i]),
            }
            for i in order
        ]

    # helpers 
    @staticmethod
    def _str(v):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return "NA"
        return str(v)

    @staticmethod
    def _keyable(v):
        """Normalize a value so it matches the keys we stored in the lookup dicts."""
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return v

    @staticmethod
    def _numeric(v):
        if v is None:
            return float("nan")
        if isinstance(v, (int, float, np.integer, np.floating)):
            return float(v)
        # strings that remained unencoded shouldn't happen, but guard anyway
        try:
            return float(v)
        except (TypeError, ValueError):
            return float("nan")
