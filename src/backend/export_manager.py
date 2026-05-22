import json
from pathlib import Path
import pandas as pd
import numpy as np  # Add for type conversion

def make_serializable(obj):
    """Recursively convert numpy types to Python built-ins for JSON serialization."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def export_dataset(df, file_name, output_dir="data/processed"):
    Path(output_dir).mkdir(exist_ok=True)
    export_path = Path(output_dir) / f"cleaned_{file_name}"
    df.to_csv(export_path, index=False)
    return str(export_path)

def export_logs(change_log, session_id):
    log_file = Path("logs/cleaning_history.json")
    log_file.parent.mkdir(exist_ok=True)  # Ensure logs dir exists
    history = {}
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:  # Check if not empty
                    history = json.loads(content)
                # else: history remains {}
        except (json.JSONDecodeError, ValueError):
            history = {}  # Reset if corrupted
    else:
        history = {}
    
    # Convert change_log to serializable
    serializable_log = make_serializable(change_log)
    history[session_id] = serializable_log
    
    with open(log_file, 'w') as f:
        json.dump(history, f, indent=2)