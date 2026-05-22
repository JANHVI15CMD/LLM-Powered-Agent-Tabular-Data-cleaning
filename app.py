import streamlit as st
import yaml
from pathlib import Path
import pandas as pd
from src.utils.logger import setup_logger
from src.frontend.upload_ui import render_upload_panel
from src.frontend.instruction_ui import render_instruction_box
from src.frontend.preview_ui import render_preview
from src.frontend.results_ui import render_results
from src.backend.dataset_loader import load_dataset
from src.backend.instruction_parser import prepare_prompt
from src.backend.self_correction import self_correct
from src.backend.validator import validate_results
from src.backend.export_manager import export_dataset, export_logs
import time
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="AI Data Cleaning Agent",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(102, 126, 234, 0.4);
    }
    .upload-section {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
    }
    .step-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        margin-right: 0.5rem;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        border-left: 4px solid #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load configs
with open("config/settings.yaml") as f:
    settings = yaml.safe_load(f)

with open("config/prompts.yaml") as f:
    prompts_config = yaml.safe_load(f)

logger = setup_logger()

# Header
st.markdown('<h1 class="main-header"> AI Data Cleaning Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Transform messy data into clean datasets with natural language instructions</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    image = Image.open("pic.jpg")
    desired_size = (240, 140) # Example: 400px width, 200px height

    # Resize the image
    resized_image = image.resize(desired_size)
    st.image(resized_image)
    st.markdown("##  Configuration")
    
    # LLM Provider selection
    provider = st.selectbox(
        " LLM Provider",
        ["gemini", "openai"],
        index=0 if settings['llm']['provider'] == "gemini" else 1
    )
    settings['llm']['provider'] = provider
    
    # Model selection based on provider
    if provider == "gemini":
        model_options = ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    else:
        model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
    
    model = st.selectbox(" Model", model_options)
    settings['llm']['model'] = model
    
    # Temperature slider
    temperature = st.slider(
        " Temperature",
        min_value=0.0,
        max_value=1.0,
        value=settings['llm']['temperature'],
        step=0.1,
        help="Lower = more deterministic, Higher = more creative"
    )
    settings['llm']['temperature'] = temperature
    
    # Max retries
    max_retries = st.slider(
        " Max Retries",
        min_value=1,
        max_value=5,
        value=settings['llm']['max_retries'],
        help="Number of self-correction attempts"
    )
    settings['llm']['max_retries'] = max_retries
    
    st.markdown("---")
    
    # Statistics
    if 'df_original' in st.session_state and st.session_state['df_original'] is not None:
        st.markdown("###  Dataset Stats")
        df = st.session_state['df_original']
        st.metric("Total Rows", f"{len(df):,}")
        st.metric("Total Columns", len(df.columns))
        st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    st.markdown("---")
    st.markdown("###  Quick Tips")
    with st.expander(" Example Instructions"):
        st.markdown("""
        - Remove all rows with null values
        - Drop duplicate rows based on email column
        - Filter rows where Age > 18
        - Remove columns: ID, Timestamp
        - Fill missing values in Salary with mean
        - Convert Date column to datetime
        - Remove outliers from Price column
        """)

# Initialize session state
if 'df_original' not in st.session_state:
    st.session_state['df_original'] = None
    st.session_state['df_cleaned'] = None
    st.session_state['change_log'] = None
    st.session_state['session_id'] = f"session_{int(time.time())}"
    st.session_state['cleaning_history'] = []

# Main content area with tabs
tab1, tab2, tab3 = st.tabs([" Clean Data", " History", "About"])

with tab1:
    # Step 1: Upload
    st.markdown('<span class="step-badge">Step 1</span> **Upload Your Dataset**', unsafe_allow_html=True)
    upload_success = render_upload_panel(settings)
    
    st.markdown("---")
    
    # Step 2: Instruction
    if upload_success or st.session_state['df_original'] is not None:
        st.markdown('<span class="step-badge">Step 2</span> **Enter Cleaning Instruction**', unsafe_allow_html=True)
        process_success = render_instruction_box()
        
        if process_success and 'instruction' in st.session_state:
            with st.spinner(" AI is generating and executing cleaning code..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                df = st.session_state['df_original'].copy()
                profile = st.session_state['profile']
                file_path = st.session_state['file_path']
                
                status_text.text(" Generating code...")
                progress_bar.progress(25)
                
                cleaned_df, code, error = self_correct(
                    df, st.session_state['instruction'], profile, prompts_config, settings, max_retries
                )
                
                progress_bar.progress(75)
                status_text.text(" Validating results...")
                
                if error:
                    progress_bar.progress(100)
                    st.markdown(f'<div class="error-box"> <strong>Error after {max_retries} attempts:</strong><br>{error}</div>', unsafe_allow_html=True)
                    st.code(code, language="python")
                else:
                    # Validate
                    changes = validate_results(df, cleaned_df, st.session_state['instruction'])
                    # add meta fields
                    changes['code_used'] = code
                    changes['instruction'] = st.session_state['instruction']
                    changes['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")

                    # Ensure top-level convenience fields exist (pull from basic_metrics if present)
                    basic = changes.get('basic_metrics', {})

                    # Convert to native python types to avoid numpy / pandas types in JSON
                    changes.setdefault('rows_before', int(basic.get('rows_before', 0)))
                    changes.setdefault('rows_after', int(basic.get('rows_after', 0)))
                    changes.setdefault('rows_removed', int(basic.get('rows_removed', 0)))
                    changes.setdefault('rows_removed_percentage', float(basic.get('rows_removed_percentage', 0.0)))

                    changes.setdefault('columns_before', int(basic.get('columns_before', 0)))
                    changes.setdefault('columns_after', int(basic.get('columns_after', 0)))

                    changes.setdefault('nulls_before', int(basic.get('nulls_before', 0)))
                    changes.setdefault('nulls_after', int(basic.get('nulls_after', 0)))
                    changes.setdefault('nulls_reduced', int(basic.get('nulls_reduced', 0)))

                    changes.setdefault('duplicates_before', int(basic.get('duplicates_before', 0)))
                    changes.setdefault('duplicates_after', int(basic.get('duplicates_after', 0)))
                    changes.setdefault('duplicates_reduced', int(basic.get('duplicates_reduced', 0)))

                    # Store cleaned df and change log
                    st.session_state['df_cleaned'] = cleaned_df
                    st.session_state['change_log'] = changes
                    st.session_state['cleaning_history'].append({
                        'instruction': st.session_state['instruction'],
                        'timestamp': changes['timestamp'],
                        'changes': changes
                    })
                    
                    # Export
                    file_name = Path(file_path).name
                    export_path = export_dataset(cleaned_df, file_name)
                    export_logs(changes, st.session_state['session_id'])
                    
                    progress_bar.progress(100)
                    status_text.text(" Cleaning completed!")
                    
                    logger.info(f"Cleaning completed: {changes}")
                    st.balloons()
        
        st.markdown("---")
        
        # Step 3: Preview
        st.markdown('<span class="step-badge">Step 3</span> **Compare Results**', unsafe_allow_html=True)
        render_preview(st.session_state.get('df_original'), st.session_state.get('df_cleaned'))
        
        st.markdown("---")
        
        # Step 4: Results
        st.markdown('<span class="step-badge">Step 4</span> **Review & Download**', unsafe_allow_html=True)
        render_results(st.session_state.get('change_log'))
    else:
        st.info(" Please upload a dataset to begin")

with tab2:
    st.markdown("##  Cleaning History")
    
    if st.session_state.get('cleaning_history'):
        # iterate reversed so latest is first
        for idx, entry in enumerate(reversed(st.session_state['cleaning_history']), 1):
            with st.expander(f" Operation {idx}: {entry.get('instruction','')[:50]}...", expanded=(idx==1)):
                st.markdown(f"** Timestamp:** {entry.get('timestamp', 'N/A')}")
                st.markdown(f"** Instruction:** {entry.get('instruction', 'N/A')}")
                
                changes = entry.get('changes', {}) or {}
                # Use .get() with defaults to avoid KeyError and ensure native types
                rows_before = int(changes.get('rows_before', 0))
                rows_after = int(changes.get('rows_after', 0))
                nulls_reduced = int(changes.get('nulls_reduced', 0))
                duplicates_reduced = int(changes.get('duplicates_reduced', 0))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Rows Changed", f"{(rows_after - rows_before):+,}")
                with col2:
                    st.metric("Nulls Reduced", f"{nulls_reduced:+,}")
                with col3:
                    st.metric("Duplicates Removed", f"{duplicates_reduced:+,}")
                
                # Show code directly instead of a nested expander
                st.markdown("####  Generated Code")
                st.code(changes.get('code_used', 'N/A'), language="python")
    else:
        st.info("No cleaning operations performed yet")


with tab3:
    st.markdown("##  About This Agent")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ###  Features
        - **AI-Powered**: Uses advanced LLMs (Gemini/GPT)
        - **Self-Correcting**: Automatically fixes errors
        - **Secure Sandbox**: Safe code execution
        - **Data Profiling**: Automatic quality analysis
        - **Validation**: Comprehensive result checking
        - **Export**: Download cleaned data & logs
        """)
    
    with col2:
        st.markdown("""
        ###  How It Works
        1. **Upload** your messy CSV dataset
        2. **Describe** what you want in plain English
        3. **AI generates** pandas code automatically
        4. **Review** changes and download results
        
        ###  Technologies
        - Streamlit for UI
        - Pandas for data processing
        - OpenAI/Gemini for code generation
        """)
    
   
