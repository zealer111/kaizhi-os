# Generated by Django 2.0.2 on 2018-06-01 11:37

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_card_comment_package'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='create_time',
            field=models.DateTimeField(default=datetime.datetime(2018, 6, 1, 11, 37, 55, 83185), verbose_name='创建时间'),
        ),
    ]
