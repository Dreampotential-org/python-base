# Generated by Django 3.1.4 on 2022-09-14 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0012_remove_channel_about'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='about',
            field=models.CharField(blank=True, default='Please add something about channel here', max_length=1000),
        ),
    ]
