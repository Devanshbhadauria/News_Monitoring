# Generated by Django 5.0.4 on 2024-04-13 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='client',
        ),
        migrations.AddField(
            model_name='company',
            name='client',
            field=models.ManyToManyField(to='main.client'),
        ),
    ]
