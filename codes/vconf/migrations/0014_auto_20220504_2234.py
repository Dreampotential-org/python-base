# Generated by Django 3.1.4 on 2022-05-04 22:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vconf', '0013_auto_20220426_1920'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='roominfo',
            table='roominfo',
        ),
        migrations.AlterModelTable(
            name='roomrecording',
            table='roomrecording',
        ),
        migrations.AlterModelTable(
            name='roomvisitors',
            table='roomvisitors',
        ),
    ]