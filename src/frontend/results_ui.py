import streamlit as st
import json
import numpy as np
from src.backend.export_manager import export_dataset


def convert_to_serializable(obj):
    """Recursively convert NumPy / pandas types to Python built-ins."""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj


def render_results(change_log):
    """Enhanced results display with detailed statistics."""
    
    if change_log:
        # Safely extract metrics
        rows_before = int(change_log.get('rows_before', 0))
        rows_after = int(change_log.get('rows_after', 0))
        nulls_before = int(change_log.get('nulls_before', 0))
        nulls_after = int(change_log.get('nulls_after', 0))
        nulls_reduced = int(change_log.get('nulls_reduced', 0))
        duplicates_before = int(change_log.get('duplicates_before', 0))
        duplicates_after = int(change_log.get('duplicates_after', 0))
        duplicates_reduced = int(change_log.get('duplicates_reduced', 0))

        # Summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">Rows Processed</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0 0 0;">
                    {0:,} → {1:,}
                </p>
                <p style="margin: 0; font-size: 0.9rem;">
                    {2:+,} rows ({3:+.1f}%)
                </p>
            </div>
            """.format(
                rows_before,
                rows_after,
                rows_after - rows_before,
                ((rows_after - rows_before) / rows_before * 100) if rows_before > 0 else 0
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">Null Values</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0 0 0;">
                    {0:,} → {1:,}
                </p>
                <p style="margin: 0; font-size: 0.9rem;">
                    {2:+,} nulls removed
                </p>
            </div>
            """.format(
                nulls_before,
                nulls_after,
                nulls_reduced
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        padding: 1.5rem; border-radius: 10px; color: white;">
                <h3 style="margin: 0; font-size: 1.2rem;">Duplicates</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0 0 0;">
                    {0:,} → {1:,}
                </p>
                <p style="margin: 0; font-size: 0.9rem;">
                    {2:+,} duplicates removed
                </p>
            </div>
            """.format(
                duplicates_before,
                duplicates_after,
                duplicates_reduced
            ), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Validation status
        validation_status = change_log.get('validation', True)
        if validation_status:
            st.success(" **Validation Passed:** Operation successfully applied")
        else:
            st.warning(" **Validation Warning:** Please review the changes carefully")
        
        # Generated code
        with st.expander(" View Generated Code", expanded=True):
            st.code(change_log.get('code_used', 'No code available'), language="python")
        
        # Download section
        st.markdown("###  Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'df_cleaned' in st.session_state and st.session_state['df_cleaned'] is not None:
                csv = st.session_state['df_cleaned'].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=" Download Cleaned CSV",
                    data=csv,
                    file_name="cleaned_dataset.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if change_log:
                serializable_log = convert_to_serializable(change_log)
                log_json = json.dumps(serializable_log, indent=2)
                st.download_button(
                    label=" Download Cleaning Log",
                    data=log_json,
                    file_name="cleaning_log.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    else:
        st.info(" Results will appear here after cleaning")
