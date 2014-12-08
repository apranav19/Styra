# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('styracore', '0003_remove_route_styra_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='styra_user',
            field=models.ForeignKey(default=-1, to='styracore.StyraUser'),
            preserve_default=True,
        ),
    ]
