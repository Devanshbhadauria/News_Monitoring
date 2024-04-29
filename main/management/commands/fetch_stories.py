from django.core.management.base import BaseCommand
from ...models import Source
from ...utils import fetch_stories


class Command(BaseCommand):
    help = 'Fetch stories from all sources'

    def handle(self, *args, **kwargs):
        # Get all sources
        sources = Source.objects.all()
        for source in sources:
            a = fetch_stories(source)
            self.stdout.write(self.style.SUCCESS(f'Successfully fetched stories from source: {source.name} Count = {a}'))
