from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.sms_webhook import twilio_inbound

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhooks/twilio/sms/', twilio_inbound, name='twilio_inbound'),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('members/', include('members.urls')),
    path('manage/', include('manage_panel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
