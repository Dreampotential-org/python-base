# Generated by Django 3.1.4 on 2021-02-25 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses_api', '0039_merge_20210224_0449'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flashcard',
            name='answer',
            field=models.CharField(max_length=300),
        ),
    ]
