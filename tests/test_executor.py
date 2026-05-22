import pytest
from src.backend.code_executor import execute_code
from src.utils.sandbox import safe_exec
import pandas as pd

def test_execute_code():
    df = pd.DataFrame({"A": [1, None]})
    code = "df = df.dropna(subset=['A'])"
    result = execute_code(df, code)
    assert len(result) == 1