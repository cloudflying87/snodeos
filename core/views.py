from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ClubStats, Officer, Sponsor, TrailWorkLog
from .forms import ContactForm


def home(request):
    stats = ClubStats.objects.first()
    officers = Officer.objects.all()
    sponsors = Sponsor.objects.filter(is_active=True)
    context = {'stats': stats, 'officers': officers, 'sponsors': sponsors}
    return render(request, 'core/home.html', context)


def about(request):
    officers = Officer.objects.all()
    return render(request, 'core/about.html', {'officers': officers})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent! We will get back to you soon.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})


def trail_work(request):
    logs = TrailWorkLog.objects.all()
    return render(request, 'core/trail_work.html', {'logs': logs})
