# Generated by Django 3.1.4 on 2021-04-11 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('neighbormade', '0008_auto_20210317_0415'),
    ]

    operations = [
        migrations.AddField(
            model_name='neighborhood',
            name='zipcode',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='neighborhood',
            name='name',
            field=models.CharField(max_length=250, null=True),
        ),
    ]