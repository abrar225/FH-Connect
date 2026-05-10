import re
from dataclasses import dataclass
from typing import Optional

from app.modules.intelligence.intent_llm import ALL_PARTICIPANTS_ASSIGNEE, TaskIntent, _resolve_assignee_name


@dataclass
class PreprocessResult:
    intent: TaskIntent
    source: str = "deterministic"


def _deadline(text: str) -> Optional[str]:
    match = re.search(r"\b(by|before|on)\s+([A-Za-z0-9 ,/-]{2,40})$", text, flags=re.I)
    return match.group(2).strip(" .") if match else None


def _find_target_task_id(title: str, active_drafts: list) -> Optional[str]:
    title_lower = title.lower()
    for draft in active_drafts:
        draft_title = str(draft.get("title") or "")
        if draft_title and (draft_title.lower() in title_lower or title_lower in draft_title.lower()):
            return str(draft.get("id"))
    return None


def detect_deterministic_intent(
    transcript_text: str,
    speaker: str = "Unknown",
    active_drafts: list | None = None,
    active_users: list | None = None,
) -> Optional[PreprocessResult]:
    active_drafts = active_drafts or []
    active_users = active_users or []
    text = transcript_text.strip()
    normalized = re.sub(r"\s+", " ", text)

    cancel_match = re.search(r"\b(cancel|forget|remove|delete|drop)\s+(?:the\s+)?(?:task\s+)?(.+)$", normalized, re.I)
    if cancel_match:
        title = cancel_match.group(2).strip(" .")
        return PreprocessResult(TaskIntent(
            action="CANCEL",
            title=title,
            target_task_id=_find_target_task_id(title, active_drafts),
            confidence=0.9,
        ))

    update_match = re.search(r"\b(?:change|update|move|reassign)\s+(?:that|this|the task|task)?\s*(?:to|as)?\s*(.+)$", normalized, re.I)
    if update_match and active_drafts:
        title = update_match.group(1).strip(" .")
        return PreprocessResult(TaskIntent(
            action="UPDATE",
            title=title,
            target_task_id=_find_target_task_id(title, active_drafts),
            confidence=0.78 if not _find_target_task_id(title, active_drafts) else 0.88,
        ))

    assign_to = re.search(r"\bassign\s+(.+?)\s+to\s+([A-Za-z][A-Za-z .'-]+)(?:\s+by\s+(.+))?$", normalized, re.I)
    please_do = re.search(r"^([A-Za-z][A-Za-z .'-]+),?\s+(?:please\s+)?(?:handle|do|build|prepare|create|finish)\s+(.+)$", normalized, re.I)
    self_do = re.search(r"\b(?:i will|i'll|i can|let me)\s+(?:handle|do|build|prepare|create|finish)\s+(.+)$", normalized, re.I)

    if assign_to:
        title = assign_to.group(1).strip(" .")
        raw_assignee = assign_to.group(2).strip(" .")
        return PreprocessResult(TaskIntent(
            action="CREATE",
            title=title,
            assignee=_resolve_assignee_name(raw_assignee, speaker, active_users),
            deadline=assign_to.group(3) or _deadline(normalized),
            confidence=0.92,
        ))

    if please_do:
        raw_assignee = please_do.group(1).strip(" .")
        title = please_do.group(2).strip(" .")
        return PreprocessResult(TaskIntent(
            action="CREATE",
            title=title,
            assignee=_resolve_assignee_name(raw_assignee, speaker, active_users),
            deadline=_deadline(normalized),
            confidence=0.9,
        ))

    if self_do:
        title = self_do.group(1).strip(" .")
        return PreprocessResult(TaskIntent(
            action="CREATE",
            title=title,
            assignee=_resolve_assignee_name("me", speaker, active_users) or speaker,
            deadline=_deadline(normalized),
            confidence=0.88,
        ))

    team_match = re.search(r"\b(?:everyone|all participants|team)\s+(?:please\s+)?(?:handle|do|prepare|review)\s+(.+)$", normalized, re.I)
    if team_match:
        return PreprocessResult(TaskIntent(
            action="CREATE",
            title=team_match.group(1).strip(" ."),
            assignee=ALL_PARTICIPANTS_ASSIGNEE,
            deadline=_deadline(normalized),
            confidence=0.88,
        ))

    return None
