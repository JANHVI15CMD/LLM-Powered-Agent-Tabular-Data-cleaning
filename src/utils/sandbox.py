import ast
import signal
import pandas as pd
import platform
from contextlib import contextmanager
from typing import Any, Dict, Optional

class TimeoutException(Exception):
    """Raised when code execution times out."""
    pass

class RestrictedExecutionError(Exception):
    """Raised when code contains disallowed operations."""
    pass

@contextmanager
def timeout(seconds):
    """Context manager for timeout handling."""
    def signal_handler(signum, frame):
        raise TimeoutException(f"Execution timed out after {seconds} seconds")
    
    # Only works on Unix-like systems
    if platform.system() != 'Windows':
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
    
    try:
        yield
    finally:
        if platform.system() != 'Windows':
            signal.alarm(0)

class SafeCodeValidator:
    """Validates that code only contains allowed operations."""
    
    ALLOWED_MODULES = {'pd', 'pandas', 'numpy', 'np'}
    
    # Python 3.x compatible - removed ast.Exec and ast.Eval
    DISALLOWED_NODES = {
        ast.Import,
        ast.ImportFrom,
        ast.Delete,
        ast.Global,
        ast.Nonlocal,
    }
    
    DISALLOWED_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__',
        'open', 'input', 'raw_input',
        'execfile', 'reload', 'vars', 'dir',
        'globals', 'locals', 'delattr', 'setattr'
    }
    
    @classmethod
    def validate(cls, code):
        """Validate that code is safe to execute."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise RestrictedExecutionError(f"Syntax error in code: {e}")
        
        for node in ast.walk(tree):
            # Check for disallowed node types
            if type(node) in cls.DISALLOWED_NODES:
                raise RestrictedExecutionError(
                    f"Disallowed operation: {type(node).__name__}"
                )
            
            # Check for disallowed function calls
            if isinstance(node, ast.Call):
                func_name = cls._get_function_name(node)
                if func_name in cls.DISALLOWED_FUNCTIONS:
                    raise RestrictedExecutionError(
                        f"Disallowed function call: {func_name}"
                    )
            
            # Check for dangerous attribute access
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_') and node.attr not in ['_merge']:
                    raise RestrictedExecutionError(
                        f"Access to private attributes not allowed: {node.attr}"
                    )
    
    @staticmethod
    def _get_function_name(call_node):
        """Extract function name from Call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None

def safe_exec(code, globals_dict, timeout_seconds=30):
    """Execute code safely in a restricted environment."""
    # Validate code safety
    SafeCodeValidator.validate(code)
    
    # Create restricted environment
    restricted_globals = {
        'pd': pd,
        'df': globals_dict.get('df'),
        '__builtins__': {
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'True': True,
            'False': False,
            'None': None,
            'print': print,
        }
    }
    
    # Execute with timeout (only on Unix-like systems)
    if platform.system() != 'Windows':
        with timeout(timeout_seconds):
            exec(code, restricted_globals)
    else:
        # On Windows, execute without signal-based timeout
        exec(code, restricted_globals)
    
    # Return modified DataFrame
    result = restricted_globals.get('df')
    if result is not None and isinstance(result, pd.DataFrame):
        return result
    
    return globals_dict.get('df')
