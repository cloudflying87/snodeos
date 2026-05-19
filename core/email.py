from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _site_url():
    return getattr(settings, 'SITE_URL', 'https://snodeos.flyhomemnlab.com').rstrip('/')


def _notification_email():
    return getattr(settings, 'NOTIFICATION_EMAIL', '') or settings.DEFAULT_FROM_EMAIL


def send_email(subject, to, template, context=None):
    """Render an HTML email template and send it. Falls back gracefully on error."""
    ctx = {'site_url': _site_url(), 'site_name': 'Brainerd Snodeos', **(context or {})}
    try:
        html_body = render_to_string(f'emails/{template}.html', ctx)
        text_body = render_to_string(f'emails/{template}.txt', ctx)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to] if isinstance(to, str) else to,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        logger.info('Email sent: %s → %s', subject, to)
    except Exception as exc:
        logger.error('Failed to send email "%s" to %s: %s', subject, to, exc)


def notify_new_application(member):
    """Tell officers a new membership application arrived."""
    recipient = _notification_email()
    if not recipient:
        return
    send_email(
        subject=f'New Membership Application — {member.get_full_name()}',
        to=recipient,
        template='new_application',
        context={
            'member': member,
            'review_url': f'{_site_url()}/members/pending/',
        },
    )


def notify_application_approved(member):
    """Tell the applicant their membership was approved."""
    send_email(
        subject='Your Brainerd Snodeos Membership Has Been Approved!',
        to=member.email,
        template='application_approved',
        context={
            'member': member,
            'login_url': f'{_site_url()}/accounts/login/',
        },
    )


def notify_contact_message(contact_msg):
    """Tell officers a contact form message arrived."""
    recipient = _notification_email()
    if not recipient:
        return
    send_email(
        subject=f'New Contact Message — {contact_msg.subject}',
        to=recipient,
        template='contact_message',
        context={
            'msg': contact_msg,
            'detail_url': f'{_site_url()}/manage/messages/',
        },
    )


def send_test_email(to):
    """Send a test email to verify SMTP config is working."""
    send_email(
        subject='Test Email — Brainerd Snodeos',
        to=to,
        template='test_email',
        context={},
    )
