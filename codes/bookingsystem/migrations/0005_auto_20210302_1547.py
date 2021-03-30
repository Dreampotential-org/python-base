# Generated by Django 3.1.4 on 2021-03-02 23:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookingsystem', '0004_auto_20210222_1429'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stadium',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('capacity', models.IntegerField()),
                ('city', models.CharField(max_length=250)),
                ('state', models.CharField(blank=True, max_length=250, null=True)),
                ('country', models.CharField(max_length=250)),
                ('region', models.CharField(max_length=250)),
                ('teams', models.CharField(max_length=250)),
                ('sports', models.CharField(max_length=250)),
                ('image', models.CharField(max_length=1000)),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='stadium',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bookingsystem.stadium'),
        ),
    ]