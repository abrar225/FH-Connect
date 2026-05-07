from pydantic import ValidationError

from app.modules.draft.rules import process_intent
from app.modules.intelligence.intent_llm import TaskIntent


def test_task_intent_rejects_unknown_action():
    try:
        TaskIntent(action="EXECUTE_TOOL", confidence=1.0)
    except ValidationError:
        return
    raise AssertionError("TaskIntent accepted an unsafe action")


def test_low_confidence_intent_is_dropped():
    intent = TaskIntent(action="CREATE", title="Prepare launch checklist", confidence=0.2)

    action, payload = process_intent(intent, "Prepare launch checklist", "room-a")

    assert action is None
    assert payload is None


def test_create_intent_produces_room_scoped_draft():
    intent = TaskIntent(
        action="CREATE",
        title="Prepare launch checklist",
        assignee="Asha",
        confidence=0.95,
    )

    action, payload = process_intent(intent, "Asha prepare the launch checklist", "room-a")

    assert action == "CREATE"
    assert payload.room_id == "room-a"
    assert payload.title == "Prepare launch checklist"
    assert payload.assignee == "Asha"
