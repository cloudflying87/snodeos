"""Twilio inbound-SMS webhook.

Twilio POSTs a form-encoded request to this view whenever someone texts our
Twilio number. We:
  1. Verify the request was actually signed by Twilio (X-Twilio-Signature).
  2. Look up the auth token to validate against — first from SiteSettings
     (DB), then from settings.TWILIO_AUTH_TOKEN as a fallback.
  3. Save the message as an InboundSMS row, keyed on Twilio's MessageSid so
     a re-delivered webhook doesn't insert twice.
  4. Optionally email the officer notification address so someone knows to
     check the inbox.
  5. Return an empty TwiML response — Twilio uses this to decide whether to
     auto-reply. We don't auto-reply.

The endpoint is intentionally public (Twilio can't authenticate) but we
require a valid signature.
"""
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import InboundSMS, SiteSettings

logger = logging.getLogger(__name__)


def _twilio_auth_token():
    """Return whichever Twilio auth token is currently configured."""
    cfg = SiteSettings.get()
    return cfg.twilio_auth_token or getattr(settings, 'TWILIO_AUTH_TOKEN', '')


def _validate_signature(request):
    """Returns True if X-Twilio-Signature matches what we'd compute from the request."""
    token = _twilio_auth_token()
    if not token:
        # No token configured — we can't validate. Refuse rather than accept
        # spoofed traffic.
        return False
    signature = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
    if not signature:
        return False

    try:
        from twilio.request_validator import RequestValidator
    except ImportError:
        logger.error('twilio package not installed — inbound SMS webhook will reject all requests')
        return False

    validator = RequestValidator(token)

    # Twilio signs the FULL URL the request was made to. Behind our nginx +
    # cloudflared chain, request.build_absolute_uri() yields the correct
    # https://yourdomain.com/... URL because SECURE_PROXY_SSL_HEADER is set.
    url = request.build_absolute_uri()
    return validator.validate(url, request.POST, signature)


@csrf_exempt
@require_POST
def twilio_inbound(request):
    if not _validate_signature(request):
        logger.warning('Rejected unsigned/invalid Twilio webhook from %s',
                       request.META.get('REMOTE_ADDR'))
        return HttpResponseForbidden('Invalid signature')

    sid          = request.POST.get('MessageSid', '').strip()
    from_number  = request.POST.get('From', '').strip()
    body         = request.POST.get('Body', '').strip()

    if not from_number or not body:
        # Malformed; ignore but return 200 so Twilio doesn't retry forever
        return HttpResponse('<Response/>', content_type='application/xml')

    msg, created = InboundSMS.objects.get_or_create(
        twilio_message_sid=sid or f'no-sid-{from_number}-{body[:30]}',
        defaults={'from_number': from_number, 'body': body},
    )

    if created:
        logger.info('Inbound SMS from %s: %s', from_number, body[:60])
        _notify_officers(msg)

    # Empty TwiML = Twilio sends no auto-reply
    return HttpResponse('<Response/>', content_type='application/xml')


def _notify_officers(msg):
    """Email the officer notification address about a new inbound SMS."""
    from .email import send_email, _tmpl_override, _notification_email
    recipient = _notification_email()
    if not recipient:
        return
    sender_label = msg.member.get_full_name() if msg.member else msg.from_number
    try:
        send_email(
            subject=f'New text from {sender_label}',
            to=recipient,
            template='inbound_sms',
            context={
                'msg': msg,
                'sender_label': sender_label,
                'inbox_url': f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/manage/sms-inbox/",
                **_tmpl_override('template_member'),
            },
        )
    except Exception as exc:
        logger.error('Failed to notify officers about inbound SMS: %s', exc)
