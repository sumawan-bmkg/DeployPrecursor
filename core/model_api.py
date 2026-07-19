"""Model API — BaseModel interface + factory for all operational models."""
from typing import Dict, Any, Optional, List
import numpy as np


class BaseModel:
    def __init__(self, name="base", params=None):
        self.name = name
        self.params = params or {}
        self._is_fitted = False
    
    def fit(self, X, y): raise NotImplementedError
    def predict(self, X): raise NotImplementedError
    def predict_proba(self, X): raise NotImplementedError
    def explain(self, X, feature_names=None) -> Dict: raise NotImplementedError
    def calibrate(self, X_val, y_val): raise NotImplementedError
    
    def evaluate(self, X_test, y_test) -> Dict[str, Any]:
        from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                     f1_score, roc_auc_score, brier_score_loss)
        y_pred = self.predict(X_test)
        r = {"n_test": len(y_test)}
        try:
            r["accuracy"] = round(accuracy_score(y_test, y_pred), 4)
            r["precision"] = round(precision_score(y_test, y_pred, zero_division=0), 4)
            r["recall"] = round(recall_score(y_test, y_pred, zero_division=0), 4)
            r["f1"] = round(f1_score(y_test, y_pred, zero_division=0), 4)
        except: pass
        try:
            yp = self.predict_proba(X_test)
            yp = yp[:, 1] if yp.ndim > 1 and yp.shape[1] >= 2 else yp
            r["auc_roc"] = round(roc_auc_score(y_test, yp), 4)
            r["brier"] = round(brier_score_loss(y_test, yp), 4)
        except: pass
        return r


class LogisticRegressionModel(BaseModel):
    def fit(self, X, y):
        from sklearn.linear_model import LogisticRegression
        self._model = LogisticRegression(max_iter=1000, random_state=42, **self.params)
        self._model.fit(X, y)
        self._is_fitted = True
        return self
    def predict(self, X): return self._model.predict(X)
    def predict_proba(self, X): return self._model.predict_proba(X)
    def explain(self, X, feature_names=None):
        fn = feature_names or [f"f{i}" for i in range(self._model.coef_.shape[1])]
        return {"type": "coefficient", "coefficients": dict(zip(fn, self._model.coef_[0])),
                "intercept": float(self._model.intercept_[0])}
    def calibrate(self, X_val, y_val): return self


class LightGBMModel(BaseModel):
    def fit(self, X, y):
        import lightgbm as lgb
        p = {"objective": "binary", "metric": "auc", "boosting_type": "gbdt",
             "num_leaves": 31, "learning_rate": 0.05, "feature_fraction": 0.8,
             "bagging_fraction": 0.8, "bagging_freq": 5, "verbose": -1,
             "random_state": 42, **self.params}
        self._model = lgb.LGBMClassifier(**p)
        self._model.fit(X, y)
        self._is_fitted = True
        return self
    def predict(self, X): return self._model.predict(X)
    def predict_proba(self, X): return self._model.predict_proba(X)
    def explain(self, X, feature_names=None):
        fn = feature_names or [f"f{i}" for i in range(len(self._model.feature_importances_))]
        return {"type": "feature_importance",
                "gain": dict(zip(fn, self._model.feature_importances_.tolist()))}
    def calibrate(self, X_val, y_val):
        from sklearn.isotonic import IsotonicRegression
        ys = self._model.predict_proba(X_val)[:, 1]
        self._calibrator = IsotonicRegression(out_of_bounds="clip")
        self._calibrator.fit(ys, y_val)
        return self


class RandomForestModel(BaseModel):
    def fit(self, X, y):
        from sklearn.ensemble import RandomForestClassifier
        self._model = RandomForestClassifier(n_estimators=100, random_state=42, **self.params)
        self._model.fit(X, y)
        self._is_fitted = True
        return self
    def predict(self, X): return self._model.predict(X)
    def predict_proba(self, X): return self._model.predict_proba(X)
    def explain(self, X, feature_names=None):
        fn = feature_names or [f"f{i}" for i in range(len(self._model.feature_importances_))]
        return {"type": "feature_importance",
                "importance": dict(zip(fn, self._model.feature_importances_.tolist()))}


MODEL_REGISTRY = {
    "logistic_regression": LogisticRegressionModel,
    "lightgbm": LightGBMModel,
    "random_forest": RandomForestModel,
}

def create_model(model_type: str, name: Optional[str] = None,
                 params: Optional[Dict] = None) -> BaseModel:
    if model_type not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_type}. Available: {list(MODEL_REGISTRY.keys())}")
    return MODEL_REGISTRY[model_type](name=name or model_type, params=params)
