from app.modules.intelligence.intent_llm import TaskIntent
from app.modules.draft.models import TaskDraft
from app.core.config import settings

def process_intent(intent_result: TaskIntent, original_transcript: str, room_id: str):
    """
    Validates the AI intent and returns (action, payload).
    """
    if intent_result.confidence < settings.INTENT_CONFIDENCE_THRESHOLD:
        return None, None

    action = intent_result.action.upper()
    
    if action == "CREATE":
        if not intent_result.title or len(intent_result.title.strip()) < 3:
            return None, None
        
        draft = TaskDraft(
            room_id=room_id,
            original_transcript=original_transcript,
            title=intent_result.title,
            assignee=intent_result.assignee,
            deadline=intent_result.deadline
        )
        return "CREATE", draft

    if action == "UPDATE" or action == "CANCEL":
        # We allow target_task_id to be missing here so the orchestrator 
        # in transcript.py can attempt to perform fuzzy matching.
        return action, intent_result

    return None, None
