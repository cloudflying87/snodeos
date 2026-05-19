"""Lightweight rate limiting using Django's cache framework.

Per-process (LocMemCache) is fine for our scale: the limits are anti-spam /
anti-double-send safeguards, not a strict security control. Three gunicorn
workers means worst-case limits are 3x the configured value — still far
below what would constitute abuse for this site.
"""
from django.core.cache import cache


def get_client_ip(request):
    """Best-effort client IP. Honors X-Forwarded-For when behind nginx/Cloudflare."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def throttle(key, max_count, window_seconds):
    """Increment a rate-limit counter under `key`. Returns True if the action
    is allowed (under the limit), False if blocked.

    On first call within the window, the counter is created with the TTL set
    to window_seconds. Subsequent calls within that window increment it.
    """
    full_key = f'throttle:{key}'
    count = cache.get(full_key, 0)
    if count >= max_count:
        return False
    if count == 0:
        cache.set(full_key, 1, timeout=window_seconds)
    else:
        try:
            cache.incr(full_key)
        except ValueError:
            cache.set(full_key, count + 1, timeout=window_seconds)
    return True


def reset(key):
    cache.delete(f'throttle:{key}')
