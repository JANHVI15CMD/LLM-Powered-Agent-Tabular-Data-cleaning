import streamlit as st
import pandas as pd
from pathlib import Path
from src.backend.dataset_loader import load_dataset

def render_upload_panel(settings):
    """Enhanced upload panel with better visuals."""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            " Choose a CSV file",
            type=["csv"],
            help="Upload your dataset in CSV format (max 200MB)",
            label_visibility="collapsed"
        )
    
    with col2:
        if st.session_state.get('df_original') is not None:
            if st.button(" Clear Dataset", use_container_width=True):
                st.session_state['df_original'] = None
                st.session_state['df_cleaned'] = None
                st.session_state['profile'] = None
                st.rerun()
    
    if uploaded_file is not None:
        # Save to raw directory
        raw_dir = Path(settings['paths']['raw_data'])
        raw_dir.mkdir(exist_ok=True)
        file_path = raw_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Load and profile
        try:
            df, profile = load_dataset(str(file_path))

            # ✅ NEW FIX: prevent empty or unreadable dataset crash
            if df is None or df.empty:
                st.error("Uploaded file is empty or unreadable. Please upload a valid CSV.")
                return False
            
            st.session_state['df_original'] = df
            st.session_state['profile'] = profile
            st.session_state['file_path'] = str(file_path)
            
            # Success message
            st.success(f" Successfully uploaded: **{uploaded_file.name}**")
            
            # Display overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(" Rows", f"{len(df):,}")
            with col2:
                st.metric(" Columns", len(df.columns))
            with col3:
                null_count = df.isnull().sum().sum()
                st.metric(" Null Values", f"{null_count:,}")
            with col4:
                dup_count = len(df[df.duplicated()])
                st.metric(" Duplicates", f"{dup_count:,}")
            
            # Data Quality Score
            quality_score = profile.get('data_quality_score', 0)
            st.progress(quality_score / 100)
            
            if quality_score >= 80:
                quality_label = " Excellent"
                quality_color = "green"
            elif quality_score >= 60:
                quality_label = " Good"
                quality_color = "orange"
            else:
                quality_label = " Needs Cleaning"
                quality_color = "red"
            
            st.markdown(f"**Data Quality Score:** :{quality_color}[{quality_label} ({quality_score:.1f}/100)]")
            
            # Show dataset preview
            with st.expander(" Preview Dataset", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)
            
            # Show detailed profile
            with st.expander(" Detailed Profile"):
                # Column information
                st.markdown("#### Column Analysis")
                
                col_data = []
                for col, info in profile['columns'].items():
                    col_data.append({
                        'Column': col,
                        'Type': info['dtype'],
                        'Nulls': f"{info['null_count']} ({info['null_percentage']:.1f}%)",
                        'Unique': info['unique_count'],
                        'Sample': str(df[col].iloc[0])[:30] if len(df) > 0 else 'N/A'
                    })
                
                st.dataframe(pd.DataFrame(col_data), use_container_width=True)
                
                # Anomalies
                if profile.get('anomalies'):
                    st.markdown("####  Detected Issues")
                    anomalies = profile['anomalies']
                    
                    if anomalies.get('high_null_columns'):
                        st.warning(f"**High null percentage:** {', '.join([a['column'] for a in anomalies['high_null_columns']])}")
                    
                    if anomalies.get('constant_columns'):
                        st.info(f"**Constant columns:** {', '.join(anomalies['constant_columns'])}")
                    
                    if anomalies.get('high_cardinality_columns'):
                        st.info(f"**High cardinality:** {', '.join([a['column'] for a in anomalies['high_cardinality_columns']])}")
            
            return True
            
        except Exception as e:
            st.error(f" Error loading file: {e}")
            return False
    
    return False
