# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Instruction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('instruction', models.CharField(max_length=512)),
                ('step_duration', models.CharField(max_length=128)),
                ('step_distance', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mode_of_transport', models.CharField(max_length=128)),
                ('time_of_travel', models.DateField(auto_now_add=True)),
                ('origin', models.CharField(max_length=512)),
                ('destination', models.CharField(max_length=512)),
                ('route_duration', models.CharField(max_length=128)),
                ('route_distance', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='instruction',
            name='route',
            field=models.ForeignKey(to='styracore.Route'),
            preserve_default=True,
        ),
    ]
