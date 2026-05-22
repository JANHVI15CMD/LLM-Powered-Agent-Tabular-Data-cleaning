from src.backend.llm_interface import get_llm_client, generate_code, generate_fixed_code
from src.backend.code_executor import execute_code
from src.backend.instruction_parser import prepare_prompt
import logging

logger = logging.getLogger(__name__)

def self_correct(df, instruction, profile, prompts_config, settings, max_retries=3):
    """
    Execute instruction with self-correction.
    
    Returns:
        Tuple of (cleaned_df, final_code, error_message)
    """
    client = get_llm_client(settings)
    initial_prompt = prepare_prompt(instruction, profile, prompts_config)
    code = generate_code(client, initial_prompt, settings)
    
    logger.info(f"Generated initial code:\n{code}")
    
    for attempt in range(max_retries):
        try:
            # Execute code
            cleaned_df = execute_code(df, code)
            logger.info(f"Code executed successfully on attempt {attempt + 1}")
            return cleaned_df, code, None  # Success
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt == max_retries - 1:
                # Final attempt failed
                logger.error(f"All {max_retries} attempts failed")
                return df, code, error_msg
            
            # Generate fixed code
            logger.info(f"Generating fix for attempt {attempt + 2}")
            try:
                fixed_code = generate_fixed_code(
                    client, error_msg, code, instruction, 
                    profile, prompts_config, settings
                )
                code = fixed_code
            except Exception as fix_error:
                logger.error(f"Error generating fix: {fix_error}")
                return df, code, f"Fix generation failed: {fix_error}"
    
    # Should not reach here
    return df, code, "Maximum retries exceeded"
