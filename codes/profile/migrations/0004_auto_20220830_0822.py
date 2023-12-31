# Generated by Django 3.1.4 on 2022-08-30 08:22

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profile', '0003_user_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='image',
            field=models.CharField(blank=True, default='https://cdn.icon-icons.com/icons2/2643/PNG/512/male_boy_person_people_avatar_icon_159358.png', max_length=500, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='userprofile',
            unique_together={('user', 'phone_number')},
        ),
    ]
