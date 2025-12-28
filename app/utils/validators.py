"""Validation utilities"""
from typing import Tuple

def validate_text_input(text: str, min_length: int = 1, max_length: int = 10000) -> Tuple[bool, str]:
    """Validate text input for mind map creation"""
    if not text:
        return False, "Text cannot be empty"
    
    if len(text) < min_length:
        return False, f"Text must be at least {min_length} characters"
    
    if len(text) > max_length:
        return False, f"Text must be at most {max_length} characters"
    
    return True, ""

def validate_node_label(label: str) -> Tuple[bool, str]:
    """Validate node label"""
    if not label or not label.strip():
        return False, "Label cannot be empty"
    
    if len(label) > 200:
        return False, "Label must be at most 200 characters"
    
    return True, ""

