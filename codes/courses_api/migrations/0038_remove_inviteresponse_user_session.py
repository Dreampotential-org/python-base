# Generated by Django 3.1.4 on 2021-02-16 07:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses_api', '0037_inviteresponse'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inviteresponse',
            name='user_session',
        ),
    ]
