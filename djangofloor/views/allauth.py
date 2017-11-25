# noinspection PyPackageRequirements
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.DF_ALLOW_USER_CREATION and settings.DF_ALLOW_LOCAL_USERS
