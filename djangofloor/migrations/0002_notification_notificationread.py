# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-15 21:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0008_alter_user_username_max_length'),
        ('djangofloor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(blank=True, default='', verbose_name='Content')),
                ('title', models.CharField(blank=True, default='', max_length=255, verbose_name='Title')),
                ('icon', models.FileField(blank=True, default=None, help_text='Not used yet', max_length=255, null=True, upload_to='notification_icons', verbose_name='Icon')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Only active notifications will be displayed.', verbose_name='Is active?')),
                ('not_before', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Do not display before')),
                ('not_after', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Do not display after')),
                ('level', models.CharField(choices=[('success', 'Success'), ('info', 'Info'), ('warning', 'Warning'), ('danger', 'Danger')], default='info', max_length=10, verbose_name='Level')),
                ('auto_hide_seconds', models.IntegerField(blank=True, default=0, help_text='Automatically hide after this number of seconds, 0 meaning no auto-hide', verbose_name='Timeout')),
                ('display_mode', models.CharField(choices=[('notification', 'HTML notification'), ('modal', 'Blocking (modal) window'), ('system', 'System notification'), ('banner', 'Screen-wide banner')], default='notification', help_text='System notifications can be hidden by users.', max_length=20, verbose_name='Display mode')),
                ('broadcast_mode', models.IntegerField(blank=True, choices=[(0, 'Any visitor (using cookies)'), (1, 'Any authenticated users'), (2, 'Selected groups and users')], db_index=True, default=2, verbose_name='Broadcast mode')),
                ('repeat_count', models.IntegerField(blank=True, db_index=True, default=1, help_text='Display count (0 meaning that the notification will always be displayed)', verbose_name='Repeat count')),
                ('author', models.ManyToManyField(blank=True, db_index=True, related_name='notification_author', to=settings.AUTH_USER_MODEL)),
                ('destination_groups', models.ManyToManyField(blank=True, db_index=True, to='auth.Group', verbose_name='Groups of users that should read this message')),
                ('destination_users', models.ManyToManyField(blank=True, db_index=True, to=settings.AUTH_USER_MODEL, verbose_name='Users that should read this message')),
            ],
        ),
        migrations.CreateModel(
            name='NotificationRead',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_read_time', models.DateTimeField(auto_now_add=True, verbose_name='first read time')),
                ('last_read_time', models.DateTimeField(auto_now=True, verbose_name='last read time')),
                ('read_count', models.IntegerField(db_index=True, default=1, verbose_name='Read count')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='djangofloor.Notification')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User that read this notification')),
            ],
        ),
    ]
