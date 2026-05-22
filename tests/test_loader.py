import pytest
from src.backend.dataset_loader import load_dataset
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "test.csv"
    df = pd.DataFrame({"A": [1, 2], "B": [None, 4]})
    df.to_csv(path, index=False)
    return str(path)

def test_load_dataset(sample_csv):
    df, profile = load_dataset(sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert 'shape' in profile
    assert profile['shape'] == (2, 2)