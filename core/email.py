import json
import logging
import urllib.request
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def _site_url():
    return getattr(settings, 'SITE_URL', 'https://snodeos.flyhomemnlab.com').rstrip('/')


def _cfg():
    from core.models import SiteSettings
    return SiteSettings.get()


def _notification_email():
    cfg = _cfg()
    if cfg.notification_email:
        return cfg.notification_email
    return getattr(settings, 'NOTIFICATION_EMAIL', '') or settings.DEFAULT_FROM_EMAIL


def _send_via_resend(api_key, from_email, to_list, subject, text_body, html_body):
    payload = json.dumps({
        'from': from_email,
        'to': to_list if isinstance(to_list, list) else [to_list],
        'subject': subject,
        'text': text_body,
        'html': html_body,
    }).encode()
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    )
    urllib.request.urlopen(req, timeout=15)


def _get_smtp_connection(cfg):
    """Return a Django email connection using DB-stored Brevo SMTP credentials."""
    return get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host='smtp-relay.brevo.com',
        port=587,
        username=cfg.notification_email or settings.EMAIL_HOST_USER,
        password=cfg.brevo_smtp_key,
        use_tls=True,
        fail_silently=False,
    )


def _email_brand_ctx():
    """Returns email branding vars pulled from DB settings."""
    cfg = _cfg()
    return {
        'email_from_name':    cfg.email_from_name    or 'Brainerd Snodeos',
        'email_header_color': cfg.email_header_color or '#1363A2',
        'email_accent_color': cfg.email_accent_color or '#1363A2',
        'email_footer_text':  cfg.email_footer_text  or "You're receiving this as a member of the Brainerd Snodeos.",
    }


def _tmpl_override(cfg_attr):
    """Return branding context dict from a SiteSettings template FK (e.g. 'template_member'), or {} if unset."""
    cfg = _cfg()
    tmpl = getattr(cfg, cfg_attr, None)
    if not tmpl:
        return {}
    return {
        'email_from_name':         tmpl.from_name,
        'email_header_color':      tmpl.header_color,
        'email_accent_color':      tmpl.accent_color,
        'email_header_image_url':  tmpl.header_image_url,
        'email_footer_text':       tmpl.footer_text,
    }


def send_email(subject, to, template, context=None):
    """
    Render an HTML email template and send it.
    Priority: Resend API → Brevo SMTP (DB) → Django default backend (.env).
    """
    ctx = {
        'site_url': _site_url(),
        'site_name': 'Brainerd Snodeos',
        **_email_brand_ctx(),
        **(context or {}),
    }
    to_list = [to] if isinstance(to, str) else to

    try:
        html_body = render_to_string(f'emails/{template}.html', ctx)
        text_body = render_to_string(f'emails/{template}.txt', ctx)
    except Exception as exc:
        logger.error('Failed to render email template "%s": %s', template, exc)
        return

    cfg = _cfg()
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        if cfg.resend_api_key:
            _send_via_resend(cfg.resend_api_key, from_email, to_list, subject, text_body, html_body)
        elif cfg.brevo_smtp_key:
            conn = _get_smtp_connection(cfg)
            msg = EmailMultiAlternatives(subject=subject, body=text_body,
                                         from_email=from_email, to=to_list,
                                         connection=conn)
            msg.attach_alternative(html_body, 'text/html')
            msg.send()
        else:
            msg = EmailMultiAlternatives(subject=subject, body=text_body,
                                         from_email=from_email, to=to_list)
            msg.attach_alternative(html_body, 'text/html')
            msg.send()
        logger.info('Email sent: %s → %s', subject, to)
    except Exception as exc:
        logger.error('Failed to send email "%s" to %s: %s', subject, to, exc)


def send_plain(subject, to, body):
    """Send a plain-text email (for blasts and reminders)."""
    to_list = [to] if isinstance(to, str) else to
    cfg = _cfg()
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        if cfg.resend_api_key:
            _send_via_resend(cfg.resend_api_key, from_email, to_list, subject, body, f'<pre>{body}</pre>')
        elif cfg.brevo_smtp_key:
            from django.core.mail import send_mail
            conn = _get_smtp_connection(cfg)
            msg = EmailMultiAlternatives(subject=subject, body=body,
                                         from_email=from_email, to=to_list,
                                         connection=conn)
            msg.send()
        else:
            from django.core.mail import send_mail
            send_mail(subject, body, from_email, to_list, fail_silently=True)
        return True
    except Exception as exc:
        logger.error('Failed to send plain email "%s" to %s: %s', subject, to, exc)
        return False


def send_sms(body, phone):
    """Send an SMS. Uses Brevo API or Twilio, preferring Brevo."""
    cfg = _cfg()
    phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not phone.startswith('+'):
        phone = '+1' + phone

    if cfg.brevo_api_key:
        payload = json.dumps({
            'type': 'transactional', 'unicodeEnabled': True,
            'sender': 'Snodeos', 'recipient': phone, 'content': body,
        }).encode()
        req = urllib.request.Request(
            'https://api.brevo.com/v3/transactionalSMS/sms',
            data=payload,
            headers={'api-key': cfg.brevo_api_key, 'Content-Type': 'application/json'},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as exc:
            logger.error('Brevo SMS failed to %s: %s', phone, exc)
            return False

    elif cfg.twilio_account_sid:
        try:
            from twilio.rest import Client
            client = Client(cfg.twilio_account_sid, cfg.twilio_auth_token)
            client.messages.create(body=body, from_=cfg.twilio_from_number, to=phone)
            return True
        except Exception as exc:
            logger.error('Twilio SMS failed to %s: %s', phone, exc)
            return False

    # Fall back to env vars
    brevo_key = getattr(settings, 'BREVO_API_KEY', '')
    twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    if brevo_key:
        payload = json.dumps({
            'type': 'transactional', 'unicodeEnabled': True,
            'sender': 'Snodeos', 'recipient': phone, 'content': body,
        }).encode()
        req = urllib.request.Request(
            'https://api.brevo.com/v3/transactionalSMS/sms',
            data=payload,
            headers={'api-key': brevo_key, 'Content-Type': 'application/json'},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception:
            return False
    elif twilio_sid:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, getattr(settings, 'TWILIO_AUTH_TOKEN', ''))
            client.messages.create(body=body, from_=getattr(settings, 'TWILIO_FROM_NUMBER', ''), to=phone)
            return True
        except Exception:
            return False
    return False


def send_test_email(to):
    send_email('Test Email — Brainerd Snodeos', to, 'test_email', {})


def notify_new_application(member):
    recipient = _notification_email()
    if not recipient:
        return
    send_email(
        subject=f'New Membership Application — {member.get_full_name()}',
        to=recipient, template='new_application',
        context={'member': member, 'review_url': f'{_site_url()}/members/pending/'},
    )


def notify_application_approved(member):
    send_email(
        subject='Your Brainerd Snodeos Membership Has Been Approved!',
        to=member.email, template='application_approved',
        context={
            'member': member,
            'login_url': f'{_site_url()}/accounts/login/',
            **_tmpl_override('template_member'),
        },
    )


def notify_contact_message(contact_msg):
    recipient = _notification_email()
    if not recipient:
        return
    send_email(
        subject=f'New Contact Message — {contact_msg.subject}',
        to=recipient, template='contact_message',
        context={'msg': contact_msg, 'detail_url': f'{_site_url()}/manage/messages/'},
    )
