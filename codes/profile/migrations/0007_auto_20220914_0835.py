# Generated by Django 3.1.4 on 2022-09-14 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0006_auto_20220914_0829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='about',
            field=models.CharField(blank=True, default='Available', max_length=256, null=True),
        ),
    ]
