from django.core.management.base import BaseCommand
from ...models import Story


class Command(BaseCommand):
    help = 'Deletes old stories if the number exceeds the limit.'

    def handle(self, *args, **options):
        max_stories = 100
        current_count = Story.objects.count()
        if current_count > max_stories:
            excess_stories = current_count - max_stories
            oldest_stories = Story.objects.order_by('created_on')[:excess_stories]

            oldest_stories_ids = oldest_stories.values_list('id', flat=True)

            for story_id in oldest_stories_ids:
                Story.objects.filter(id=story_id).delete()



            self.stdout.write(self.style.SUCCESS(f'{excess_stories} old stories deleted.'))
