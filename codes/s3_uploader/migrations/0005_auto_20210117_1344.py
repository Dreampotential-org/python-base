# Generated by Django 3.1.4 on 2021-01-17 13:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('s3_uploader', '0004_auto_20210117_1339'),
    ]

    operations = [
        migrations.RenameField(
            model_name='roomvisitors',
            old_name='name',
            new_name='user_name',
        ),
    ]