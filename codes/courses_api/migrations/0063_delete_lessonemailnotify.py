# Generated by Django 3.1.4 on 2022-05-18 17:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses_api', '0062_flashcard_is_required'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LessonEmailNotify',
        ),
    ]