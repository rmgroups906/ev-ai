import pytest
import pandas as pd
from app.ml.model import load_model 
@pytest.fixture(scope="session")
def model():
    """Fixture to load the ML model once for the entire test session."""
    return load_model()

@pytest.fixture(scope="session")
def golden_dataset():
    """
    Fixture to load a 'golden' dataset for testing.
    This should be a representative, static sample of your data.
    """
    data = {
        'feature1': [1, 3, 5, 2.5, 6],
        'feature2': [2, 4, 6, 4.5, 5.5],
        'label': [0, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    X_test = df[['feature1', 'feature2']]
    y_true = df['label']
    return X_test, y_true