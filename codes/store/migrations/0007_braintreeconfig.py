# Generated by Django 2.2.8 on 2021-01-26 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_auto_20201212_1431'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrainTreeConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('braintree_merchant_ID', models.CharField(max_length=70)),
                ('braintree_public_key', models.CharField(max_length=70)),
                ('braintree_private_key', models.CharField(max_length=70)),
            ],
        ),
    ]