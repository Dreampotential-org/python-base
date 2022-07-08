# Generated by Django 3.1.4 on 2022-06-02 12:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0034_auto_20220602_1751'),
        ('courses_api', '0065_auto_20220602_1751'),
    ]

    operations = [
        migrations.DeleteModel(
            name='StripeItem',
        ),
        migrations.AddField(
            model_name='stripeproductprice',
            name='flashcard_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses_api.flashcard'),
        ),
    ]