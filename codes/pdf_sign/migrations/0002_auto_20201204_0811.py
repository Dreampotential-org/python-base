# Generated by Django 2.2.8 on 2020-12-04 02:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf_sign', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='doc',
            name='ref_firm_comm',
            field=models.IntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='doc',
            name='listing_firm_commission',
            field=models.IntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='doc',
            name='other',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='doc',
            name='selling_firm_commission',
            field=models.IntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
    ]
