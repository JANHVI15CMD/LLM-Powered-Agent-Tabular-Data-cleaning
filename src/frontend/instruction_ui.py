import streamlit as st

def render_instruction_box():
    """Enhanced instruction input with suggestions."""
    
    # Pre-defined examples
    examples = [
        "Remove all rows with null values",
        "Drop duplicate rows based on email column",
        "Filter rows where Age > 18",
        "Remove columns: ID, Timestamp, Notes",
        "Fill missing values in Salary column with median",
        "Convert Date column to datetime format",
        "Remove outliers from Price column using IQR method",
        "Standardize text in Name column to title case",
        "Keep only rows where Status is 'Active'",
        "Drop rows where City is null or empty"
    ]
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("###  What do you want to do?")
    
    with col2:
        example_select = st.selectbox(
            "Quick Examples",
            ["Select an example..."] + examples,
            label_visibility="collapsed"
        )
    
    # Instruction text area
    if example_select != "Select an example...":
        default_value = example_select
    else:
        default_value = st.session_state.get('last_instruction', '')
    
    instruction = st.text_area(
        "Natural Language Instruction",
        value=default_value,
        height=120,
        placeholder="Example: Remove all rows where Age is null and City is empty",
        help="Describe the cleaning operation you want to perform in plain English",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        execute_button = st.button(
            " Clean Data",
            type="primary",
            use_container_width=True,
            disabled=(not instruction or 'df_original' not in st.session_state)
        )
    
    with col2:
        if st.button(" Clear Instruction", use_container_width=True):
            st.session_state['last_instruction'] = ''
            st.rerun()
    
    if execute_button:
        if instruction and 'df_original' in st.session_state:
            st.session_state['instruction'] = instruction
            st.session_state['last_instruction'] = instruction
            return True
        else:
            st.warning(" Please upload a dataset first!")
    
    return False
