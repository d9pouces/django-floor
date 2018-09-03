import importlib
import os
from collections import OrderedDict
from configparser import RawConfigParser
from typing import Union

SOCIAL_PROVIDER_APPS = {
    "allauth.socialaccount.providers.%s" % x
    for x in {
        "amazon",
        "angellist",
        "asana",
        "auth0",
        "baidu",
        "basecamp",
        "bitbucket",
        "bitbucket_oauth2",
        "bitly",
        "coinbase",
        "digitalocean",
        "discord",
        "douban",
        "draugiem",
        "edmodo",
        "eveonline",
        "evernote",
        "facebook",
        "feedly",
        "flickr",
        "foursquare",
        "fxa",
        "github",
        "gitlab",
        "google",
        "hubic",
        "instagram",
        "kakao",
        "line",
        "linkedin",
        "linkedin_oauth2",
        "mailru",
        "mailchimp",
        "naver",
        "odnoklassniki",
        "openid",
        "orcid",
        "paypal",
        "persona",
        "pinterest",
        "reddit",
        "robinhood",
        "shopify",
        "slack",
        "soundcloud",
        "spotify",
        "stackexchange",
        "stripe",
        "tumblr",
        "twentythreeandme",
        "twitch",
        "twitter",
        "untappd",
        "vimeo",
        "vk",
        "weibo",
        "weixin",
        "windowslive",
        "xing",
    }
}


class SocialProviderConfiguration:
    help = "Please read https://django-allauth.readthedocs.io/en/latest/providers.html#{{ provider_id }}\n" "Contact {{ provider_name }} to get authentication secrets. " "Callback URL should be {{ SERVER_BASE_URL }}accounts/{{ provider_id }}/login/callback/"
    attributes = {
        "client_id": "App ID, or consumer key",
        "secret": "API secret, client secret, or consumer secret",
        "key": "Key (often optional)",
    }
    name_prefix = "df-"

    def __init__(
        self,
        provider_id: str,
        provider_name: str,
        provider_app: str,
        values: Union[dict, None] = None,
    ):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.provider_app = provider_app
        self.values = values

    def __str__(self):
        return self.provider_name

    @property
    def name(self):
        return "%s%s" % (self.name_prefix, self.provider_name)

    def query_kwargs(self):
        return {"name": self.name, "provider": self.provider_id}

    @property
    def help_text(self):
        from djangofloor.conf.settings import merger
        from django.template import Template, Context

        context = {}
        context.update(merger.settings)
        context.update(self.__dict__)
        return Template(self.help).render(Context(dict_=context))


def get_available_configurations() -> dict:
    """return a dict of all existing social account provider configurations"""
    existing_providers = {}
    available_configurations = {x.id: x for x in SOCIAL_PROVIDER_CONFIGURATIONS}
    for provider_app in SOCIAL_PROVIDER_APPS:
        try:
            provider_module = importlib.import_module("%s.provider" % provider_app)
            for provider_cls in getattr(provider_module, "provider_classes", []):
                config_cls = available_configurations.get(
                    provider_cls.id, SocialProviderConfiguration
                )
                config = config_cls(provider_cls.id, provider_cls.name, provider_app)
                existing_providers[provider_cls.id] = config
        except ImportError:
            pass
    return existing_providers


def get_loaded_configurations() -> OrderedDict:
    """return a list of configured social authentication backends from a config file
    given in settings.ALLAUTH_APPLICATIONS_CONFIG
    """
    from django.conf import settings

    parser = RawConfigParser()
    if os.path.isfile(settings.ALLAUTH_APPLICATIONS_CONFIG):
        parser.read([settings.ALLAUTH_APPLICATIONS_CONFIG])

    existing_providers = get_available_configurations()
    providers = OrderedDict()
    for section in parser.sections():
        if section not in existing_providers:
            continue
        provider_config = existing_providers[section]
        values = {
            key: parser.get(section, key)
            for key in parser.options(section)
            if key in provider_config.attributes
        }
        provider_config.values = values
        providers[provider_config.provider_id] = provider_config
    return providers


def migrate(read_only: bool = False) -> bool:
    """
    Create and configure database social apps.

    Configure backends only for the first Site object.

    :param read_only:
    :return: True if (read_only and a migrate is required) or (not read_only and modifications were performed)
    """
    # noinspection PyPackageRequirements
    from allauth.socialaccount.models import SocialApp

    # noinspection PyPackageRequirements
    from django.contrib.sites.models import Site

    expected_configurations = {}
    for config in get_loaded_configurations().values():
        expected_configurations[(config.name, config.provider_id)] = config
    action_required = False
    to_remove_db_app_ids = []
    to_create_db_apps = []
    db_apps = {}
    for social_app in SocialApp.objects.filter(
        name__startswith=SocialProviderConfiguration.name_prefix
    ):
        key = (social_app.name, social_app.provider)
        if key not in expected_configurations:
            to_remove_db_app_ids.append(social_app.pk)
            continue
        else:
            db_apps[key] = social_app
    for key, configuration in expected_configurations.items():
        if key not in db_apps:
            to_create_db_apps.append(
                SocialApp(
                    name=configuration.name,
                    provider=configuration.provider_id,
                    **configuration.values
                )
            )
            continue
        app = db_apps[key]
        save = False
        for k, v in configuration.values.items():
            if getattr(app, k) != v:
                setattr(app, k, v)
                save = True
        if save:
            action_required = True
            if not read_only:
                app.save()
    if to_remove_db_app_ids:
        action_required = True
        if not read_only:
            SocialApp.objects.filter(pk__in=to_remove_db_app_ids).delete()
    if to_create_db_apps:
        action_required = True
        if not read_only:
            SocialApp.objects.bulk_create(to_create_db_apps)

    db_site = Site.objects.filter(pk=1).first()
    if db_site:
        required_db_ids = {
            x[0]
            for x in SocialApp.objects.filter(
                name__startswith=SocialProviderConfiguration.name_prefix
            ).values_list("id")
        }
        q = SocialApp.sites.through
        existing_db_ids = {
            x[0]
            for x in q.objects.filter(
                site_id=db_site.pk, socialapp_id__in=required_db_ids
            ).values_list("socialapp_id")
        }
        to_create_db_through_app = [
            q(site_id=db_site.pk, socialapp_id=x)
            for x in required_db_ids
            if x not in existing_db_ids
        ]
        if to_create_db_through_app:
            action_required = True
            if not read_only:
                q.objects.bulk_create(to_create_db_through_app)
    return action_required


class GithubConfiguration(SocialProviderConfiguration):
    id = "github"
    help = """open https://github.com/settings/applications/new and enter:
    Application name: {{ DF_PROJECT_NAME }} ({{ SERVER_NAME }})
    Homepage URL: {{ SERVER_BASE_URL }}
    Application description: {{ DF_PROJECT_NAME }} (or anything else useful)
    Authorization callback URL: {{ SERVER_BASE_URL }}accounts/github/login/callback/
    
    After validation, you can copy the following values:
    """
    attributes = {"client_id": "Client ID", "secret": "Client Secret"}


class FacebookConfiguration(SocialProviderConfiguration):
    id = "facebook"
    help = """open https://developers.facebook.com/apps and create an app to obtain a key and secret key.
    After registration you will need to make it available to the public. 
    In order to do that your app first has to be reviewed by Facebook.

    Leave your App Domains empty and put {{ SERVER_BASE_URL }} in the section labeled Website with Facebook Login. 
    Note that you’ll need to add your site’s actual domain to this section once it goes live.

    After validation, you can copy the following values:
    """
    attributes = {"client_id": "Client ID", "secret": "Client Secret"}


SOCIAL_PROVIDER_CONFIGURATIONS = [GithubConfiguration]
