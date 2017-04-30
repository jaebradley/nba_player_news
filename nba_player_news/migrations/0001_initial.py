# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-30 19:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('email', 'Email'), ('twitter', 'Twitter')], max_length=50)),
                ('platform_identifier', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('platform', 'platform_identifier')]),
        ),
    ]
