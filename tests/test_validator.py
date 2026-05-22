import pytest
from src.backend.validator import validate_results
import pandas as pd

def test_validate_results():
    df_orig = pd.DataFrame({"Age": [25, None]})
    df_clean = pd.DataFrame({"Age": [25]})
    changes = validate_results(df_orig, df_clean, "remove null Age")
    assert changes['validation'] == True
    assert changes['rows_after'] == 1