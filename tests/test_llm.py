import pytest
from unittest.mock import patch
from src.backend.llm_interface import generate_code

@patch('openai.OpenAI')
def test_generate_code(mock_openai):
    mock_client = mock_openai.return_value
    mock_client.chat.completions.create.return_value.choices = [type('obj', (object,), {'message': type('msg', (object,), {'content': 'df.dropna()'})})]
    code = generate_code(mock_client, "prompt", {'llm': {'model': 'test'}})
    assert code == 'df.dropna()'