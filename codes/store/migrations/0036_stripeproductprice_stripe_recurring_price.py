# Generated by Django 3.1.4 on 2022-06-24 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0035_auto_20220602_1751'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripeproductprice',
            name='stripe_recurring_price',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
