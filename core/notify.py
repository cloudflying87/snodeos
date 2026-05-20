"""Helpers for the in-site Notification model.

Use notify(user, kind, title, url) anywhere a user should see a bell-icon
alert. Never raises — notifications must not break the action that triggers
them.
"""
import logging
from .models import Notification

logger = logging.getLogger(__name__)


def notify(user, kind, title, url=''):
    if not user or not getattr(user, 'is_authenticated', False):
        return
    try:
        return Notification.objects.create(
            user=user, kind=kind, title=title[:200], url=url[:300],
        )
    except Exception as exc:
        logger.error('Failed to create Notification: %s', exc)


def context_processor(request):
    """Available in every template as {{ notif_unread_count }}."""
    count = 0
    if request.user.is_authenticated:
        try:
            count = Notification.objects.filter(user=request.user, is_read=False).count()
        except Exception:
            count = 0
    return {'notif_unread_count': count}
