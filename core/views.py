from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ClubStats, Officer, Sponsor, TrailWorkLog, Announcement
from .forms import ContactForm
from .email import notify_contact_message


def home(request):
    stats = ClubStats.objects.first()
    officers = Officer.objects.all()
    sponsors = Sponsor.objects.filter(is_active=True)
    announcements = Announcement.objects.all()[:5]
    context = {
        'stats': stats,
        'officers': officers,
        'sponsors': sponsors,
        'announcements': announcements,
    }
    return render(request, 'core/home.html', context)


def about(request):
    officers = Officer.objects.all()
    return render(request, 'core/about.html', {'officers': officers})


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
    return render(request, 'core/contact.html', {'form': form})


from django.contrib.auth.decorators import login_required

@login_required
def trail_work(request):
    logs = TrailWorkLog.objects.prefetch_related('images').all()
    return render(request, 'core/trail_work.html', {'logs': logs})
