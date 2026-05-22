from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

import os
import logging

logger = logging.getLogger(__name__)

# Debug prints
print(f"DEBUG: Current working dir: {os.getcwd()}")
print(f"DEBUG: GEMINI_API_KEY exists: {bool(os.getenv('GEMINI_API_KEY'))}")
print(f"DEBUG: OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")

# Conditional imports
if os.getenv('OPENAI_API_KEY'):
    from openai import OpenAI

import google.generativeai as genai

def get_llm_client(settings):
    """Initialize LLM client based on provider."""
    provider = settings['llm']['provider']
    
    if provider == "openai":
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Set OPENAI_API_KEY environment variable.")
        return OpenAI(api_key=api_key)
    
    elif provider == "gemini":
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Set GEMINI_API_KEY environment variable.")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(settings['llm']['model'])
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def generate_code(client, prompt, settings):
    """Generate code from LLM."""
    provider = settings['llm']['provider']
    temperature = settings['llm']['temperature']
    
    try:
        if provider == "openai":
            model = settings['llm']['model']
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            code = response.choices[0].message.content.strip()
            logger.info(f"Generated code using OpenAI {model}")
            return clean_code_output(code)
        
        elif provider == "gemini":
            # Gemini-specific prompt adaptation
            full_prompt = f"""{prompt}
            
Output ONLY the Pandas code snippet to transform 'df'. Do not add imports, explanations, or extra text."""
            
            response = client.generate_content(
                full_prompt, 
                generation_config={"temperature": temperature}
            )
            
            if response.text:
                code = response.text.strip()
                logger.info(f"Generated code using Gemini")
                return clean_code_output(code)
            else:
                raise ValueError("Gemini API returned no text response.")
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        raise

def generate_fixed_code(client, error, code, instruction, profile, prompts_config, settings):
    """Generate fixed code after error."""
    provider = settings['llm']['provider']
    schema_str = ', '.join([f"{col}:{dtype}" for col, dtype in profile['columns'].items()])
    
    if provider == "openai":
        prompt_template = prompts_config.get('error_correction', DEFAULT_ERROR_CORRECTION_PROMPT)
        prompt = prompt_template.format(
            error=error,
            code=code,
            schema=schema_str,
            instruction=instruction
        )
    
    elif provider == "gemini":
        prompt = f"""The following code failed with error: {error}

Code:
{code}

Schema: {schema_str}
Instruction: {instruction}

Fix the code and output ONLY the corrected Pandas code snippet. Do not add imports or explanations."""
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    logger.info(f"Generating fixed code for error: {error[:100]}")
    return generate_code(client, prompt, settings)

def clean_code_output(code):
    """Clean and extract code from LLM output."""
    # Remove markdown code blocks
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[3:].strip()
    
    if code.endswith("```"):
        code = code[:-3].strip()
    
    # Remove explanatory text (keep only code lines)
    lines = code.split('\n')
    code_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        # Keep lines that look like code
        if any(char in stripped for char in ['=', '(', '[', 'df', 'pd']):
            code_lines.append(line)
    
    cleaned = '\n'.join(code_lines)
    logger.debug(f"Cleaned code: {cleaned}")
    return cleaned


# Default prompt templates (fallback if not in config)
DEFAULT_ERROR_CORRECTION_PROMPT = """The following code failed with error: {error}

Code: {code}

Schema: {schema}

Instruction: {instruction}

Fix the code and output ONLY the corrected Pandas code snippet. Do not add imports or explanations."""
