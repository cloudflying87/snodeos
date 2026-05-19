import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from core.models import ClubStats, Officer, OfficerTitle, Sponsor, Announcement
from accounts.models import RegistrationField


class Command(BaseCommand):
    help = 'Seeds the database with initial club data'

    def handle(self, *args, **options):
        self._seed_stats()
        self._seed_titles()
        self._seed_registration_fields()
        self._seed_officers()
        self._seed_sponsors()
        self._seed_announcements()
        self.stdout.write(self.style.SUCCESS('Seed data loaded successfully.'))

    def _seed_titles(self):
        titles = [
            ('President',      1),
            ('Vice President', 2),
            ('Secretary',      3),
            ('Treasurer',      4),
            ('Director',       5),
        ]
        for name, order in titles:
            OfficerTitle.objects.get_or_create(name=name, defaults={'order': order})
        self.stdout.write('  Officer titles seeded')

    def _seed_registration_fields(self):
        defaults = [
            ('phone',            False, False, 1),
            ('address',          False, False, 2),
            ('city',             True,  False, 3),
            ('state',            True,  False, 4),
            ('zip_code',         False, False, 5),
            ('snowmobile_brand', True,  False, 6),
        ]
        for field_name, enabled, required, order in defaults:
            RegistrationField.objects.get_or_create(
                field_name=field_name,
                defaults={'is_enabled': enabled, 'is_required': required, 'order': order}
            )
        self.stdout.write('  Registration fields seeded')

    def _seed_stats(self):
        if not ClubStats.objects.exists():
            ClubStats.objects.create(
                members_count=125,
                miles_maintained=107,
                annual_budget=45000,
                supporting_landowners=50,
            )
            self.stdout.write('  Created ClubStats')

    def _copy_image(self, src_filename, dest_subdir):
        src = os.path.join(settings.BASE_DIR, 'static', 'images', src_filename)
        if not os.path.exists(src):
            return None
        dest_dir = os.path.join(settings.MEDIA_ROOT, dest_subdir)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, src_filename)
        shutil.copy2(src, dest)
        return os.path.join(dest_subdir, src_filename)

    def _seed_officers(self):
        officers = [
            {'name': 'John Schommer',  'title': 'President',      'snowmobile_brand': 'Polaris',  'order': 1,  'photo_file': 'officer-john.jpg'},
            {'name': 'Ryan Frank',     'title': 'Vice President',  'snowmobile_brand': 'Ski-Doo', 'order': 2,  'photo_file': 'officer-ryan.jpeg'},
            {'name': 'Nathan Hulinsky','title': 'Secretary',       'snowmobile_brand': 'Polaris',  'order': 3,  'photo_file': 'officer-nathan.jpg'},
            {'name': 'Dan Johnson',    'title': 'Treasurer',       'snowmobile_brand': 'Yamaha',   'order': 4,  'photo_file': 'officer-dan.jpg'},
            {'name': 'Steve Houle',    'title': 'Director',        'snowmobile_brand': 'Polaris',  'order': 5,  'photo_file': None},
            {'name': 'George Burton',  'title': 'Director',        'snowmobile_brand': 'Polaris',  'order': 6,  'photo_file': None},
            {'name': 'Tim M',          'title': 'Director',        'snowmobile_brand': 'Ski-Doo',  'order': 7,  'photo_file': None},
            {'name': 'Chuck Kaphing',  'title': 'Director',        'snowmobile_brand': 'Polaris',  'order': 8,  'photo_file': None},
            {'name': 'Scott Berry',    'title': 'Director',        'snowmobile_brand': 'Ski-Doo',  'order': 9,  'photo_file': None},
            {'name': 'Trent Baumann',  'title': 'Director',        'snowmobile_brand': 'Ski-Doo',  'order': 10, 'photo_file': None},
        ]
        for data in officers:
            photo_file = data.pop('photo_file')
            obj, created = Officer.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'  Created officer: {obj.name}')
            if photo_file:
                needs_photo = not obj.photo or not os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.photo.name))
                if needs_photo:
                    photo_path = self._copy_image(photo_file, 'officers')
                    if photo_path:
                        obj.photo = photo_path
                        obj.save()
                        self.stdout.write(f'  Restored photo: {obj.name}')

    def _seed_sponsors(self):
        sponsors = [
            {
                'name': 'Wild Rice Depot',
                'website': 'https://thecornerstore-it.com/contact-us/',
                'order': 1,
                'logo_file': 'hero-sled.webp',
            },
            {
                'name': 'The Woods',
                'website': 'https://www.thewoodsmn.com/brainerd-restaurant-b-merri/',
                'order': 2,
                'logo_file': 'sponsor-merri.png',
            },
            {
                'name': 'Brothers Motorsports',
                'website': 'https://www.brothersmotorsports.com',
                'order': 3,
                'logo_file': 'brothers.png',
            },
            {
                'name': 'Black Bear Lodge',
                'website': 'https://blackbearlodgemn.com',
                'order': 4,
                'logo_file': 'sponsor-blackbear.jpg',
            },
            {
                'name': 'True Photo Design',
                'website': 'https://www.truephotodesign.com',
                'order': 5,
                'logo_file': 'sponsor-true.jpg',
            },
            {
                'name': 'All Cleaning',
                'website': 'https://www.facebook.com/profile.php?id=61566113765752',
                'order': 6,
                'logo_file': 'sponsor-allcleaning.jpg',
            },
            {
                'name': 'Power Lodge',
                'website': 'https://www.powerlodgebrainerd.com/',
                'order': 7,
                'logo_file': 'sponsor-powerlodge.png',
            },
        ]
        for data in sponsors:
            logo_file = data.pop('logo_file')
            obj, created = Sponsor.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'  Created sponsor: {obj.name}')
            # Always re-copy logo if the media file is missing (e.g. after a rebuild wiped media/)
            needs_logo = not obj.logo or not os.path.exists(os.path.join(settings.MEDIA_ROOT, obj.logo.name))
            if needs_logo:
                logo_path = self._copy_image(logo_file, 'sponsors')
                if logo_path:
                    obj.logo = logo_path
                    obj.save()
                    self.stdout.write(f'  Restored logo: {obj.name}')

    def _seed_announcements(self):
        announcements = [
            {
                'title': 'Trail Season Opening',
                'body': 'Trails are now open for the season. Please ride responsibly and stay on marked trails.',
                'is_pinned': True,
            },
            {
                'title': 'Monthly Meeting Reminder',
                'body': 'Our monthly meeting is every third Monday at 7:00 PM. All members welcome!',
                'is_pinned': False,
            },
        ]
        for data in announcements:
            obj, created = Announcement.objects.get_or_create(title=data['title'], defaults=data)
            if created:
                self.stdout.write(f'  Created announcement: {obj.title}')
