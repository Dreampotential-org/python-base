# Generated by Django 3.1.4 on 2021-04-19 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_auto_20210420_0100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacheruimessage',
            name='delivered_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
