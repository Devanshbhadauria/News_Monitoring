from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Company(models.Model):
    name = models.TextField(max_length=100)

    def __str__(self):
        return self.name


class Subscribe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Company, on_delete=models.CASCADE)


class Source(models.Model):
    name = models.TextField(max_length=100)
    url = models.URLField(max_length=200)
    client = models.ForeignKey(Company, related_name='sources', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sources_created')
    created_on = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sources_updated', null=True)
    updated_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('url', 'client')

    def __str__(self):
        return self.name


class Story(models.Model):
    title = models.TextField(max_length=1000)
    pub_date = models.DateTimeField()
    body_text = models.TextField(max_length=10000)
    url = models.URLField(max_length=20000)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    companies = models.ManyToManyField(Company, related_name='stories_as_company')
    client = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories_created')
    created_on = models.DateTimeField(default=timezone.now)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories_updated', null=True)
    updated_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('url', 'client')
