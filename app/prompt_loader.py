import os
import logging
from typing import Dict, Any

logger = logging.getLogger("PromptLoader")

# Resolve absolute path to the prompts directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

def get_prompt_path(prompt_name: str) -> str:
    """
    Resolves the absolute path of a prompt file by name.
    Appends .txt if not already specified.
    """
    if not prompt_name.endswith(".txt") and not prompt_name.endswith(".md"):
        prompt_name = f"{prompt_name}.txt"
        
    candidate_path = os.path.join(PROMPTS_DIR, prompt_name)
    if os.path.exists(candidate_path):
        return candidate_path
        
    # Check fallback relative to current working directory
    cwd_candidate = os.path.join(os.getcwd(), "prompts", prompt_name)
    if os.path.exists(cwd_candidate):
        return cwd_candidate
        
    # Check parent directory prompts
    parent_candidate = os.path.join(os.path.dirname(BASE_DIR), "prompts", prompt_name)
    if os.path.exists(parent_candidate):
        return parent_candidate

    raise FileNotFoundError(f"Prompt template '{prompt_name}' not found in {PROMPTS_DIR} or search paths.")

def load_prompt(prompt_name: str, **kwargs: Any) -> str:
    """
    Dynamically loads an external prompt template from /prompts and formats with kwargs.
    
    Args:
        prompt_name (str): The filename of the prompt template (e.g., 'agrivision_advisory_v1').
        **kwargs: Substitution variables to format into the template.
        
    Returns:
        str: Fully formatted prompt text.
    """
    path = get_prompt_path(prompt_name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            template = f.read()
            
        if kwargs:
            # Format template with provided variables
            return template.format(**kwargs)
        return template
    except Exception as e:
        logger.error(f"Error loading prompt '{prompt_name}' from {path}: {str(e)}")
        raise

