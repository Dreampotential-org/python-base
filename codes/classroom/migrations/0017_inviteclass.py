# Generated by Django 3.1.4 on 2021-03-27 02:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0016_auto_20210205_0938'),
    ]

    operations = [
        migrations.CreateModel(
            name='InviteClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.TextField(unique=True)),
                ('class_invited', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='classroom.class')),
            ],
        ),
    ]
