import yaml
from pathlib import Path

def prepare_prompt(instruction, profile, prompts_config):
    schema_str = ', '.join([f"{col}:{dtype}" for col, dtype in profile['columns'].items()])
    sample_rows_str = str(profile['sample_rows'])
    
    prompt_template = prompts_config['code_generation']
    prompt = prompt_template.format(
        schema=schema_str,
        sample_rows=sample_rows_str,
        instruction=instruction
    )
    
    return prompt