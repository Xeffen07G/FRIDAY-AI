import time
from typing import Dict, Any, List

class InstantResponseLayer:
    """
    Task 1: Immediate Reaction Layer
    Generates extremely fast acknowledgments ONLY when we are sure, like greetings.
    No fake statuses allowed.
    """
    
    def __init__(self):
        pass

    def generate_instant_reaction(self, user_input: str) -> str:
        input_lower = user_input.lower().strip()
        if input_lower in ('hello', 'hi', 'hey'):
            return 'Hello.'
        return ''

instant_response_layer = InstantResponseLayer()
