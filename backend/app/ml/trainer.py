import os, joblib
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from ..config import settings
from ..model import prepare_features_single

def train_parts(csv_path: str):
    df = pd.read_csv(csv_path)
    if 'fault_type' not in df.columns:
        raise ValueError('CSV missing fault_type label column')
    X = []
    for _, r in df.iterrows():
        X.append(prepare_features_single(r.to_dict()))
    X = np.vstack(X)
    y = df['fault_type'].astype(str).to_numpy()
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    os.makedirs(settings.MODELS_DIR, exist_ok=True)
    path = os.path.join(settings.MODELS_DIR, 'parts_model.joblib')
    joblib.dump(clf, path)
    # optional S3 upload if configured
    if settings.S3_BUCKET and settings.AWS_ACCESS_KEY_ID:
        import boto3
        s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        s3.upload_file(path, settings.S3_BUCKET, 'parts_model.joblib')
    return path