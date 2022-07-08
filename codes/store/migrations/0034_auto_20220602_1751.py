# Generated by Django 3.1.4 on 2022-06-02 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0033_stripeitem_flashcard_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeProductPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_product_id', models.CharField(max_length=255)),
                ('stripe_price_id', models.CharField(max_length=255)),
                ('price', models.IntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name='stripeitem',
            name='flashcard_id',
        ),
    ]