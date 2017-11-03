"""Admin models for created notifications
======================================

You can use the default admin view to create new notifications for your users.
There are actions to activate or deactivate these notifications.
"""
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import site
from django.template.defaultfilters import truncatewords
from django.utils.translation import ugettext_lazy as _

__author__ = 'Matthieu Gallet'


class NotificationAdmin(admin.ModelAdmin):

    # noinspection PyMethodMayBeStatic
    def activate(self, request, queryset):
        n = queryset.filter(is_active=False).update(is_active=True)
        if n == 0:
            messages.info(request, _('No notification has been activated.'))
        elif n == 1:
            messages.info(request, _('A notification has been activated.'))
        else:
            messages.info(request, _('%(n)s notifications have been activated.') % {'n': n})
    activate.short_description = _('Activate the selected notifications')

    # noinspection PyMethodMayBeStatic
    def deactivate(self, request, queryset):
        n = queryset.filter(is_active=True).update(is_active=False)
        if n == 0:
            messages.info(request, _('No notification has been deactivated.'))
        elif n == 1:
            messages.info(request, _('A notification has been deactivated.'))
        else:
            messages.info(request, _('%(n)s notifications have been deactivated.') % {'n': n})
    deactivate.short_description = _('Deactivate the selected notifications')

    def title_short(self, obj):
        if obj.title:
            return truncatewords(obj.title, 10)
        return '-'
    title_short.short_description = _('Title')

    def content_short(self, obj):
        if obj.content:
            return truncatewords(obj.content, 10)
        return '-'

    def save_model(self, request, obj, form, change):
        obj.author = request.user
        obj.save()

    content_short.short_description = _('Content')
    readonly_fields = []
    exclude = ['author', 'icon']
    search_fields = ['title', ]
    filter_horizontal = ['destination_users', 'destination_groups']

    list_display = ('title_short', 'content_short', 'is_active', 'not_before', 'not_after', 'level',
                    'auto_hide_seconds', 'display_mode', 'broadcast_mode', 'repeat_count')
    list_filter = ('is_active', 'level', 'display_mode', 'broadcast_mode', 'not_before', 'not_after', 'repeat_count')
    actions = ['activate', 'deactivate']


site.site_title = _('%(project)s administration') % {'project': settings.DF_PROJECT_NAME}
site.site_header = _('%(project)s (administration)') % {'project': settings.DF_PROJECT_NAME}
# site.register(Notification, NotificationAdmin)
