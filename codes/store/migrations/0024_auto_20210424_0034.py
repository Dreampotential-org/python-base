# Generated by Django 3.1.4 on 2021-04-23 19:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0023_auto_20210420_0118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacheruimessage',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receiver', related_query_name='r', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='teacheruimessage',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sender', related_query_name='s', to=settings.AUTH_USER_MODEL),
        ),
    ]