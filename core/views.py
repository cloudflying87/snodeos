from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from .models import ClubStats, Officer, Sponsor, TrailWorkLog, Announcement
from .forms import ContactForm
from .email import notify_contact_message


def home(request):
    stats = ClubStats.objects.first()
    officers = Officer.objects.exclude(title='Director')
    sponsors = Sponsor.objects.filter(is_active=True)
    announcements = Announcement.objects.filter(
        visibility__in=['public', 'both']
    ).order_by('-is_pinned', '-created_at')[:5]
    context = {
        'stats': stats,
        'officers': officers,
        'sponsors': sponsors,
        'announcements': announcements,
    }
    return render(request, 'core/home.html', context)


def about(request):
    officers = Officer.objects.exclude(title='Director')
    directors = Officer.objects.filter(title='Director')
    return render(request, 'core/about.html', {'officers': officers, 'directors': directors})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_msg = form.save()
            notify_contact_message(contact_msg)
            messages.success(request, 'Your message has been sent! We will get back to you soon.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    contact_officers = Officer.objects.exclude(title='Director').filter(
        models.Q(email__gt='') | models.Q(phone__gt='')
    )
    return render(request, 'core/contact.html', {'form': form, 'contact_officers': contact_officers})


from django.contrib.auth.decorators import login_required

@login_required
def trail_work(request):
    logs = TrailWorkLog.objects.prefetch_related('images').all()
    return render(request, 'core/trail_work.html', {'logs': logs})
