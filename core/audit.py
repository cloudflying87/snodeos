"""Helper for writing AuditLog entries. Kept thin so views can do `log_action(...)` inline."""
import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def log_action(actor, action, target='', detail=''):
    """Write an audit log row. Never raises — auditing should not break a view."""
    try:
        AuditLog.objects.create(
            actor=actor if actor and actor.is_authenticated else None,
            action=action,
            target=str(target)[:200],
            detail=str(detail),
        )
    except Exception as exc:
        logger.error('Failed to write audit log: %s', exc)
