from django.core.management.base import BaseCommand
from core.models import ClubStats, Officer, Sponsor, Announcement


class Command(BaseCommand):
    help = 'Seeds the database with initial club data'

    def handle(self, *args, **options):
        self._seed_stats()
        self._seed_officers()
        self._seed_sponsors()
        self._seed_announcements()
        self.stdout.write(self.style.SUCCESS('Seed data loaded successfully.'))

    def _seed_stats(self):
        if not ClubStats.objects.exists():
            ClubStats.objects.create(
                members_count=125,
                miles_maintained=107,
                annual_budget=45000,
                supporting_landowners=50,
            )
            self.stdout.write('  Created ClubStats')

    def _seed_officers(self):
        officers = [
            {'name': 'John Schommer', 'title': 'President', 'snowmobile_brand': 'Polaris', 'order': 1},
            {'name': 'Ryan Frank', 'title': 'Vice President', 'snowmobile_brand': 'Ski-Doo', 'order': 2},
            {'name': 'Nathan Hulinsky', 'title': 'Secretary', 'snowmobile_brand': 'Polaris', 'order': 3},
            {'name': 'Dan Johnson', 'title': 'Treasurer', 'snowmobile_brand': 'Yamaha', 'order': 4},
        ]
        for data in officers:
            obj, created = Officer.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'  Created officer: {obj.name}')

    def _seed_sponsors(self):
        sponsors = [
            {'name': 'Brainerd Lakes Motorsports', 'order': 1},
            {'name': 'Grand View Lodge', 'order': 2},
            {'name': 'Madden\'s on Gull Lake', 'order': 3},
            {'name': 'Coco Moon Restaurant', 'order': 4},
            {'name': 'Ernie\'s Bar & Grill', 'order': 5},
        ]
        for data in sponsors:
            obj, created = Sponsor.objects.get_or_create(name=data['name'], defaults=data)
            if created:
                self.stdout.write(f'  Created sponsor: {obj.name}')

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
