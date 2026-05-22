import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from scipy import stats

def validate_results(df_original: pd.DataFrame, df_cleaned: pd.DataFrame,
                    instruction: str, code: str = None) -> Dict[str, Any]:
    """
    Full validation of cleaning results.
    """

    basic = get_basic_metrics(df_original, df_cleaned)

    validation_report = {
        'basic_metrics': basic,
        'statistical_validation': validate_statistical_consistency(df_original, df_cleaned),
        'schema_validation': validate_schema(df_original, df_cleaned),
        'instruction_alignment': validate_instruction_alignment(df_original, df_cleaned, instruction),
        'overall_valid': True,
        'warnings': [],
        'errors': []
    }

    # CRITICAL ERROR FLAG
    if basic['rows_after'] == 0:
        validation_report['errors'].append("All rows were removed - likely an error")
        validation_report['overall_valid'] = False

    # SCHEMA WARNING
    if len(validation_report['schema_validation']['columns_removed']) > len(df_original.columns) * 0.5:
        validation_report['warnings'].append("More than 50% of columns were removed")

    # INSTRUCTION CHECK
    if not validation_report['instruction_alignment']['instruction_satisfied']:
        validation_report['warnings'].append("Cleaning operation may not match instruction")

    return validation_report


# --------------------------------------------------------------------
#  BASIC METRICS (FIXED)
# --------------------------------------------------------------------
def get_basic_metrics(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> Dict[str, Any]:
    """Accurate before/after metrics for UI."""

    rows_before = int(len(df_original))
    rows_after = int(len(df_cleaned))

    cols_before = int(len(df_original.columns))
    cols_after = int(len(df_cleaned.columns))

    nulls_before = int(df_original.isnull().sum().sum())
    nulls_after = int(df_cleaned.isnull().sum().sum())

    dup_before = int(df_original.duplicated().sum())
    dup_after = int(df_cleaned.duplicated().sum())

    return {
        'rows_before': rows_before,
        'rows_after': rows_after,
        'rows_removed': rows_before - rows_after,
        'rows_removed_percentage': ((rows_before - rows_after) / rows_before * 100) if rows_before > 0 else 0,

        'columns_before': cols_before,
        'columns_after': cols_after,

        'nulls_before': nulls_before,
        'nulls_after': nulls_after,
        'nulls_reduced': nulls_before - nulls_after,

        'duplicates_before': dup_before,
        'duplicates_after': dup_after,
        'duplicates_reduced': dup_before - dup_after
    }


# --------------------------------------------------------------------
#  STATISTICAL VALIDATION
# --------------------------------------------------------------------
def validate_statistical_consistency(df_original: pd.DataFrame,
                                    df_cleaned: pd.DataFrame) -> Dict[str, Any]:
    result = {
        'numeric_distributions_preserved': True,
        'distribution_changes': {}
    }

    numeric_cols = [c for c in df_original.select_dtypes(include=[np.number]).columns
                    if c in df_cleaned.columns]

    for col in numeric_cols:
        m1 = df_original[col].mean()
        m2 = df_cleaned[col].mean()

        if pd.isna(m1) or pd.isna(m2):
            continue

        # If more than 20% drift, flag
        if abs(m1 - m2) / (abs(m1) + 1e-9) > 0.20:
            result['numeric_distributions_preserved'] = False
            result['distribution_changes'][col] = {
                'original_mean': float(m1),
                'cleaned_mean': float(m2),
                'change_percentage': float(abs(m1 - m2) / abs(m1) * 100)
            }

    return result


# --------------------------------------------------------------------
#  SCHEMA VALIDATION
# --------------------------------------------------------------------
def validate_schema(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> Dict[str, Any]:
    orig_cols = set(df_original.columns)
    new_cols = set(df_cleaned.columns)

    return {
        'columns_removed': list(orig_cols - new_cols),
        'columns_added': list(new_cols - orig_cols),
        'dtype_changes': get_dtype_changes(df_original, df_cleaned),
        'schema_preserved': orig_cols == new_cols
    }


def get_dtype_changes(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> Dict[str, Tuple[str, str]]:
    changes = {}
    common = set(df_original.columns) & set(df_cleaned.columns)

    for col in common:
        if str(df_original[col].dtype) != str(df_cleaned[col].dtype):
            changes[col] = (str(df_original[col].dtype), str(df_cleaned[col].dtype))

    return changes


# --------------------------------------------------------------------
#  INSTRUCTION ALIGNMENT
# --------------------------------------------------------------------
def validate_instruction_alignment(df_original: pd.DataFrame,
                                   df_cleaned: pd.DataFrame,
                                   instruction: str) -> Dict[str, Any]:

    inst = instruction.lower()

    alignment = {
        'instruction_satisfied': True,
        'confidence': 'medium',
        'reasoning': []
    }

    # NULL removal
    if any(k in inst for k in ['remove null', 'drop null', 'dropna', 'missing']):
        reduced = df_original.isnull().sum().sum() - df_cleaned.isnull().sum().sum()
        if reduced > 0:
            alignment['reasoning'].append(f"Nulls reduced by {reduced}")
            alignment['confidence'] = 'high'
        else:
            alignment['instruction_satisfied'] = False
            alignment['reasoning'].append("Nulls not reduced")

    # DUPLICATES
    if any(k in inst for k in ['duplicate', 'dedupe', 'drop duplicate']):
        d1 = df_original.duplicated().sum()
        d2 = df_cleaned.duplicated().sum()
        reduced = d1 - d2

        if reduced > 0:
            alignment['reasoning'].append(f"Removed {reduced} duplicates")
            alignment['confidence'] = 'high'
        else:
            alignment['instruction_satisfied'] = False
            alignment['reasoning'].append("Duplicates not removed")

    # ROW FILTERING
    if any(k in inst for k in ['filter', 'remove row', 'exclude', 'keep only']):
        diff = len(df_original) - len(df_cleaned)
        alignment['reasoning'].append(f"Row difference: {diff}")

    # COLUMN DROP
    if any(k in inst for k in ['drop column', 'remove column', 'delete column']):
        removed = len(df_original.columns) - len(df_cleaned.columns)
        alignment['reasoning'].append(f"Columns removed: {removed}")

    return alignment
