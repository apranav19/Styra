# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('styracore', '0005_auto_20141208_0643'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='styrauser',
            name='email_address',
        ),
    ]
