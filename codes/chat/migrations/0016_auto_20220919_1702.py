# Generated by Django 3.1.4 on 2022-09-19 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0015_auto_20220919_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channelmember',
            name='designation',
            field=models.CharField(choices=[('1', 'joined'), ('0', 'leave'), ('-1', 'terminated')], default='1', max_length=100),
        ),
        migrations.AlterField(
            model_name='userrequest',
            name='request_type',
            field=models.CharField(choices=[('0', 'cancel'), ('1', 'joined'), ('2', 'requested')], default='2', max_length=256),
        ),
    ]
