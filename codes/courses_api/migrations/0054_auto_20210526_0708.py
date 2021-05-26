# Generated by Django 2.2.8 on 2021-05-26 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses_api', '0053_usersession_has_verified_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='flashcard',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flashcard',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]