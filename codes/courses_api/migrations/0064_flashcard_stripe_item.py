# Generated by Django 3.1.4 on 2022-06-02 09:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0030_stripeitem'),
        ('courses_api', '0063_flashcard_stripe_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='flashcard',
            name='stripe_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.stripeitem'),
        ),
    ]
