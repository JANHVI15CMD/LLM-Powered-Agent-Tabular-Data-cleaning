import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple
from scipy import stats

def load_dataset(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load dataset and generate comprehensive profile."""
    df = pd.read_csv(file_path)
    profile = generate_comprehensive_profile(df)
    return df, profile

def generate_comprehensive_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate detailed data quality profile.
    
    Returns:
        Dictionary containing comprehensive data quality metrics
    """
    profile = {
        'shape': df.shape,
        'columns': {},
        'null_counts': df.isnull().sum().to_dict(),
        'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict(),
        'duplicates': len(df[df.duplicated()]),
        'duplicate_percentage': (len(df[df.duplicated()]) / len(df) * 100),
        'sample_rows': df.head(20).to_dict('records'),
        'data_quality_score': 0.0,
        'anomalies': {},
        'column_stats': {}
    }
    
    # Detailed column analysis
    for col in df.columns:
        col_info = {
            'dtype': str(df[col].dtype),
            'unique_count': df[col].nunique(),
            'unique_percentage': (df[col].nunique() / len(df) * 100),
            'null_count': df[col].isnull().sum(),
            'null_percentage': (df[col].isnull().sum() / len(df) * 100)
        }
        
        # Numeric column statistics
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info.update({
                'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                'median': float(df[col].median()) if not df[col].isnull().all() else None,
                'std': float(df[col].std()) if not df[col].isnull().all() else None,
                'min': float(df[col].min()) if not df[col].isnull().all() else None,
                'max': float(df[col].max()) if not df[col].isnull().all() else None,
                'has_outliers': detect_outliers(df[col])
            })
        
        # Categorical column statistics
        elif pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            top_values = df[col].value_counts().head(20).to_dict()
            col_info.update({
                'top_values': top_values,
                'cardinality': 'high' if df[col].nunique() > len(df) * 0.5 else 'low'
            })
        
        profile['columns'][col] = col_info
    
    # Calculate overall data quality score
    profile['data_quality_score'] = calculate_quality_score(df, profile)
    
    # Detect anomalies
    profile['anomalies'] = detect_data_anomalies(df, profile)
    
    return profile

def detect_outliers(series: pd.Series) -> bool:
    """Detect outliers using IQR method."""
    if series.isnull().all() or len(series.dropna()) < 4:
        return False
    
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = ((series < lower_bound) | (series > upper_bound)).sum()
    return outliers > 0

def calculate_quality_score(df: pd.DataFrame, profile: Dict) -> float:
    """
    Calculate overall data quality score (0-100).
    
    Factors:
    - Completeness (40%): Percentage of non-null values
    - Consistency (30%): Duplicate rate
    - Validity (30%): Data type consistency
    """
    # Completeness score
    total_cells = df.shape[0] * df.shape[1]
    non_null_cells = df.count().sum()
    completeness = (non_null_cells / total_cells) * 40 if total_cells > 0 else 0
    
    # Consistency score (inverse of duplicate rate)
    duplicate_rate = profile['duplicate_percentage'] / 100
    consistency = (1 - duplicate_rate) * 30
    
    # Validity score (columns with expected data types)
    validity = 30  # Simplified for now
    
    total_score = completeness + consistency + validity
    return round(total_score, 2)

def detect_data_anomalies(df: pd.DataFrame, profile: Dict) -> Dict[str, Any]:
    """Detect common data anomalies."""
    anomalies = {
        'high_null_columns': [],
        'high_cardinality_columns': [],
        'constant_columns': [],
        'suspicious_patterns': []
    }
    
    for col, info in profile['columns'].items():
        # High null percentage
        if info['null_percentage'] > 50:
            anomalies['high_null_columns'].append({
                'column': col,
                'null_percentage': info['null_percentage']
            })
        
        # Constant columns (all same value)
        if info['unique_count'] == 1:
            anomalies['constant_columns'].append(col)
        
        # High cardinality for categorical data
        if info.get('cardinality') == 'high' and info['unique_count'] > len(df) * 0.9:
            anomalies['high_cardinality_columns'].append({
                'column': col,
                'unique_percentage': info['unique_percentage']
            })
    
    return anomalies
