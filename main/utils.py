import feedparser
from dateutil.parser import parse

from .models import Story


def fetch_stories(source):
    # client = request.user.subscribe.client
    # user = request.user
    # source = Source.objects.get(id=source_id)
    feed = feedparser.parse(source.url)
    new_stories_count = 0
    for entry in feed.entries:
        existing_story = Story.objects.filter(url=entry.get('link', '')).exists()
        if existing_story is None:
            obj = Story.objects.create(
                title=entry.get('title', ''),
                body_text=entry.get('description', ''),
                source=source,
                pub_date=parse(entry['published']),
                url=entry['link'],
                client=source.client,
                created_by=source.created_by,
            )
            new_stories_count += 1

    return new_stories_count
