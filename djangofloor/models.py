"""Django models specific to DjangoFloor
=====================================

Currently, only defines models for Notification:

    * Notifications themselves,
    * NotificationRead, that tracks traces of read actions from users.

Non-authenticated users uses sessions for tracking read actions.
"""
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import F
from django.db.models import Q
from django.db.models.signals import pre_migrate, post_migrate
from django.dispatch import receiver
from django.template.defaultfilters import truncatewords
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _

from djangofloor.conf.settings import merger

__author__ = 'Matthieu Gallet'


class Notification(models.Model):
    ANY = 0
    AUTHENTICATED = 1
    SELECTED_GROUPS_OR_USERS = 2
    SYSTEM = 'system'
    NOTIFICATION = 'notification'
    MODAL = 'modal'
    POPUP = 'popup'
    BANNER = 'banner'
    SUCCESS = 'success'
    WARNING = 'warning'
    INFO = 'info'
    DANGER = 'danger'

    content = models.TextField(_('Content'), blank=True, default='')
    title = models.CharField(_('Title'), max_length=255, blank=True, default='')
    icon = models.FileField(_('Icon'), max_length=255, blank=True, null=True, default=None, help_text=_('Not used yet'),
                            upload_to='notification_icons')
    is_active = models.BooleanField(_('Is active?'), default=True, blank=True, db_index=True,
                                    help_text=_('Only active notifications will be displayed.'))
    not_before = models.DateTimeField(_('Do not display before'), db_index=True, null=True, blank=True)
    not_after = models.DateTimeField(_('Do not display after'), db_index=True, null=True, blank=True)
    level = models.CharField(_('Level'), max_length=10, default=INFO,
                             choices=((SUCCESS, _('Success')), (INFO, _('Info')),
                                      (WARNING, _('Warning')), (DANGER, _('Danger'))))
    auto_hide_seconds = models.IntegerField(_('Timeout'),
                                            blank=True, default=0,
                                            help_text=_('Automatically hide after this number of seconds, '
                                                        '0 meaning no auto-hide'))
    author = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, db_index=True,
                                    related_name='notification_author')
    display_mode = models.CharField(_('Display mode'), max_length=20, default=NOTIFICATION,
                                    choices=(
                                        (NOTIFICATION, _('HTML notification')),
                                        (MODAL, _('Blocking (modal) window')),
                                        (SYSTEM, _('System notification')),
                                        (BANNER, _('Screen-wide banner')),
                                        # (POPUP, _('Popup')),
                                    ),
                                    help_text=_('System notifications can be hidden by users.'))
    broadcast_mode = models.IntegerField(_('Broadcast mode'), blank=True, db_index=True,
                                         choices=((ANY, _('Any visitor (using cookies)')),
                                                  (AUTHENTICATED, _('Any authenticated users')),
                                                  (SELECTED_GROUPS_OR_USERS, _('Selected groups and users'))),
                                         default=SELECTED_GROUPS_OR_USERS)
    repeat_count = models.IntegerField(_('Repeat count'), db_index=True, default=1,
                                       blank=True,
                                       help_text=_('Display count (0 meaning that the notification will '
                                                   'always be displayed)'))
    destination_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, db_index=True,
                                               verbose_name=_('Users that should read this message'))
    destination_groups = models.ManyToManyField(Group, blank=True, db_index=True,
                                                verbose_name=_('Groups of users that should read this message'))

    def __str__(self):
        result = ''
        if self.title:
            result += '%s' % truncatewords(self.title, 10)
        if self.content:
            if result:
                result += ' (%s)' % truncatewords(self.content, 10)
            else:
                result += '%s' % truncatewords(self.content, 12)
        if self.not_before:
            result += ' from ' + self.not_before.strftime('%Y/%m/%d %H:%M')
        if self.not_after:
            result += ' to ' + self.not_after.strftime('%Y/%m/%d %H:%M')
        return result

    def __unicode__(self):
        return self.__str__()

    @classmethod
    def get_notifications(cls, request):
        now = datetime.datetime.now(tz=utc)
        query = cls.objects.filter(is_active=True).filter(Q(not_before=None) | Q(not_before__lte=now)) \
            .filter(Q(not_after=None) | Q(not_after__gte=now))
        if request.user.is_authenticated:
            user = request.user
            query = query.filter(Q(broadcast_mode=cls.ANY) | Q(broadcast_mode=cls.AUTHENTICATED)
                                 | Q(destination_users=user) | Q(destination_groups__in=user.groups.all()))
        else:
            query = query.filter(broadcast_mode=cls.ANY)
        notifications = list(query)
        if not notifications:
            return []
        if request.user.is_authenticated:
            read_by_pk = {}
            for read in NotificationRead.objects.filter(notification_id__in=[x.pk for x in notifications]):
                read_by_pk[read.notification_id] = read
            result = []
            new_reads = []
            updated_read_pks = []
            for notification in notifications:
                if notification.repeat_count == 0:
                    result.append(notification)
                elif notification.pk not in read_by_pk:
                    # noinspection PyUnboundLocalVariable
                    new_reads.append(NotificationRead(notification=notification, user=user))
                    result.append(notification)
                else:
                    read = read_by_pk[notification.pk]
                    if notification.repeat_count > read.read_count:
                        updated_read_pks.append(read.pk)
                        result.append(notification)
            if new_reads:
                NotificationRead.objects.bulk_create(new_reads)
            if updated_read_pks:
                NotificationRead.objects.filter(pk__in=updated_read_pks).update(read_count=F('read_count') + 1,
                                                                                last_read_time=now)
            notifications = result
        else:
            read_notification_pks = request.session.get('djangofloor_notifications', {})
            result = []
            for notification in notifications:
                pk = notification.pk
                current_count = read_notification_pks.get(pk, 0)
                if notification.repeat_count == 0:
                    result.append(notification)
                elif notification.repeat_count > current_count:
                    read_notification_pks[pk] = 1 + current_count
                    result.append(notification)
            notifications = result
            request.session['djangofloor_notifications'] = read_notification_pks
        return notifications


class NotificationRead(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('User that read this notification'),
                             db_index=True, on_delete=models.CASCADE)
    first_read_time = models.DateTimeField(_('first read time'), auto_now_add=True)
    last_read_time = models.DateTimeField(_('last read time'), auto_now=True)
    read_count = models.IntegerField(_('Read count'), default=1, db_index=True)


# noinspection PyUnusedLocal
@receiver(pre_migrate)
def apply_pre_migrate_settings(sender, **kwargs):
    """Defined for calling "pre_migrate" method on each ConfigValue setting through the "pre_migrate" Django signal."""
    if not hasattr(apply_pre_migrate_settings, 'applied'):  # must be called once, but the signal is called for all app
        merger.call_method_on_config_values('pre_migrate')
        apply_pre_migrate_settings.applied = True


# noinspection PyUnusedLocal
@receiver(post_migrate)
def apply_post_migrate_settings(sender, **kwargs):
    """Defined for calling "post_migrate" method on each ConfigValue setting through the "post_migrate" Django signal"""
    if not hasattr(apply_post_migrate_settings, 'applied'):  # must be called once, but the signal is called for all app
        merger.call_method_on_config_values('post_migrate')
        apply_post_migrate_settings.applied = True
    domain = settings.SERVER_NAME
    if (settings.SERVER_PORT != 80 and not settings.USE_SSL) or (settings.SERVER_PORT != 443 and settings.USE_SSL):
        domain = '%s:%s' % (settings.SERVER_NAME, settings.SERVER_PORT)
    Site.objects.filter(pk=1).update(name=settings.SERVER_NAME, domain=domain)
    username = getattr(settings, 'DF_FAKE_AUTHENTICATION_USERNAME', None)
    if username and settings.DEBUG and get_user_model().objects.filter(username=username).count() == 0:
        get_user_model()(username=username, is_staff=True, is_superuser=True).save()
