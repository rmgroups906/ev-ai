import numpy as np
import joblib, os
from sklearn.ensemble import IsolationForest
from .config import settings

def prepare_features_single(row: dict):
    cols = ['pack_voltage','pack_current','soc','soh','cell_temp_max','cell_temp_min','coolant_temp','motor_rpm','motor_torque','inverter_temp','speed_kph']
    vals = [float(row.get(c, 0.0)) for c in cols]
    mean = np.array(vals); std = np.zeros_like(mean); mn = np.array(vals); mx = np.array(vals)
    feat = np.concatenate([mean, std, mn, mx], axis=0)
    return feat

class AnomalyModel:
    def __init__(self, path=None):
        self.path = path or os.path.join(settings.MODELS_DIR, 'model_iforest.joblib')
        self.model = None

    def load(self):
        if os.path.exists(self.path):
            self.model = joblib.load(self.path)
            return True
        return False

    def save(self, clf):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        joblib.dump(clf, self.path)

    def predict(self, feat):
        if self.model is None:
            raise RuntimeError('Model not loaded')
        return self.model.predict(feat)

    def score(self, feat):
        if self.model is None: raise RuntimeError('Model not loaded')
        return self.model.score_samples(feat)