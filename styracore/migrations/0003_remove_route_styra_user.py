# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('styracore', '0002_auto_20141208_0629'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='route',
            name='styra_user',
        ),
    ]
