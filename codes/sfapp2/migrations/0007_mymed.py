# Generated by Django 2.2.8 on 2020-11-03 00:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sfapp2', '0006_gpscheckin'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyMed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=2000)),
                ('dosage', models.CharField(default='', max_length=2000)),
                ('member', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='sfapp2.Member')),
            ],
        ),
    ]
