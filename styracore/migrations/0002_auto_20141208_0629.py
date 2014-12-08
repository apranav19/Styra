# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('styracore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StyraUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email_address', models.EmailField(max_length=75)),
                ('phone_number', models.CharField(max_length=128)),
                ('first_name', models.CharField(max_length=128)),
                ('last_name', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='route',
            name='styra_user',
            field=models.ForeignKey(default=-1, to='styracore.StyraUser'),
            preserve_default=True,
        ),
    ]
