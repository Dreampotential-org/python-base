# Generated by Django 3.1.4 on 2022-06-02 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses_api', '0064_flashcard_stripe_item'),
        ('store', '0030_stripeitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripeitem',
            name='flashcard_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses_api.flashcard'),
        ),
    ]
