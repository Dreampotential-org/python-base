# Generated by Django 3.1.4 on 2022-05-11 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voip', '0044_twiliosession_confsid'),
    ]

    operations = [
        migrations.AddField(
            model_name='sms_details',
            name='sid',
            field=models.CharField(blank=True, max_length=512, null=True, unique=True),
        ),
    ]