# Generated by Django 3.1.4 on 2022-06-08 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SSIDReading',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('address', models.CharField(max_length=512)),
                ('channel', models.CharField(max_length=512)),
                ('quality', models.CharField(max_length=512)),
                ('building_floor', models.IntegerField(max_length=512)),
                ('quality_int', models.IntegerField(max_length=512)),
            ],
        ),
    ]