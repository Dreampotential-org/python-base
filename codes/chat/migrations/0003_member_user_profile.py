# Generated by Django 3.1.4 on 2022-08-25 09:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0003_user_profile'),
        ('chat', '0002_auto_20220825_0649'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='user_profile',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='profile.userprofile'),
        ),
    ]
