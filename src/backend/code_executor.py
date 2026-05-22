import pandas as pd
import ast
import logging
from src.utils.sandbox import safe_exec

logger = logging.getLogger(__name__)

def execute_code(df, code, timeout=30):
    """
    Execute cleaning code in sandbox.
    
    Args:
        df: Original DataFrame
        code: Pandas code to execute
        timeout: Maximum execution time
    
    Returns:
        Cleaned DataFrame
    """
    # Validate syntax first
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Invalid Python syntax: {e}")
    
    try:
        # Execute in sandbox
        result = safe_exec(code, {'df': df.copy(), 'pd': pd}, timeout_seconds=timeout)
        
        if result is None:
            raise ValueError("Code returned None instead of DataFrame")
        
        if not isinstance(result, pd.DataFrame):
            raise TypeError(f"Code returned {type(result)} instead of DataFrame")
        
        logger.info(f"Execution successful. Shape: {df.shape} -> {result.shape}")
        return result
        
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        raise
