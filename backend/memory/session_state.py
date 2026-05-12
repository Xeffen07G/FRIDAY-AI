import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("friday.memory.session_state")

class SessionState:
    """Tracks active conversational context, goals, and unresolved threads."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.active_goals: List[str] = []
        self.unresolved_questions: List[str] = []
        self.emotional_trajectory: List[str] = []
        self.recent_topics: List[str] = []
        self.last_update = datetime.now()

    def update_from_interaction(self, user_input: str, assistant_output: str, intent: str):
        """Heuristically updates the session state based on the latest interaction."""
        self.last_update = datetime.now()
        
        # Simple heuristic for goals (e.g., "I want to", "Can you help me with")
        if any(trigger in user_input.lower() for trigger in ["i want to", "i need to", "help me with", "building", "developing"]):
            self.active_goals.append(user_input[:100])
            if len(self.active_goals) > 5: self.active_goals.pop(0)

        # Simple heuristic for unresolved questions
        if "?" in user_input and len(assistant_output) < 20: # Short answer might mean unresolved
            self.unresolved_questions.append(user_input)
            if len(self.unresolved_questions) > 3: self.unresolved_questions.pop(0)
            
        # Topic tracking (simplified)
        words = [w for w in user_input.lower().split() if len(w) > 4]
        if words:
            self.recent_topics.extend(words[:3])
            if len(self.recent_topics) > 20: self.recent_topics = self.recent_topics[-20:]

    def get_context_string(self) -> str:
        """Returns a string representation of the active session state for the LLM."""
        context = []
        if self.active_goals:
            context.append(f"CURRENT GOALS: {', '.join(self.active_goals)}")
        if self.unresolved_questions:
            context.append(f"UNRESOLVED QUESTIONS: {', '.join(self.unresolved_questions)}")
        if self.recent_topics:
            context.append(f"ACTIVE TOPICS: {', '.join(set(self.recent_topics))}")
        
        return "\n".join(context)

class SessionStateManager:
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}

    def get_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id)
        return self.sessions[session_id]

session_state_manager = SessionStateManager()
