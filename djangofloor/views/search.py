"""Abstract global-site search view
================================

The DjangoFloor base template provides a site-wide search field.
The corresponding search view is defined by the setting `DF_SITE_SEARCH_VIEW` and should be a class-based view.
Here is an example of abstract class-based view, as well as a generic model search view and an example of working search
view (searching across users)

"""
import logging
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from djangofloor.tasks import set_websocket_topics
from djangofloor.forms import SearchForm

__author__ = "Matthieu Gallet"
logger = logging.getLogger("django.request")


class SiteSearchView(TemplateView):
    """Abstract site-wide search view"""

    template_name = "djangofloor/bootstrap3/search.html"
    """used template for displaying the results"""

    def get(self, request, *args, **kwargs):
        """Get method (use GET data for filling the form)"""
        return self.get_or_post(request, SearchForm(request.GET))

    def post(self, request):
        """Post method (use POST data for filling the form)"""
        return self.get_or_post(request, SearchForm(request.POST))

    def get_or_post(self, request, form):
        """Common result, the same for GET or POST data.
        Takes a bound form."""
        pattern = form.cleaned_data["q"] if form.is_valid() else None
        search_query = self.get_query(request, pattern=pattern)
        page = request.GET.get("page")
        paginator = Paginator(search_query, 25)
        try:
            paginated_results = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_results = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_results = paginator.page(paginator.num_pages)
        context = {
            "form": form,
            "paginated_url": "%s?%s"
            % (reverse("df:site_search"), urlencode({"q": pattern})),
            "paginated_results": paginated_results,
            "formatted_results": self.formatted_results(paginated_results),
            "formatted_header": self.formatted_header(),
        }
        extra_context = self.get_template_values(request)
        context.update(extra_context)
        set_websocket_topics(request)
        return self.render_to_response(context)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def get_template_values(self, request):
        """provide extra template values """
        return {}

    def formatted_results(self, paginated_results):
        """return all results in a formatted form as an iterator"""
        for obj in paginated_results:
            yield self.format_result(obj)

    def get_query(self, request, pattern):
        """given the search pattern provided by the user, return the search query """
        raise NotImplementedError

    def format_result(self, obj):
        """format a single result as a table row"""
        raise NotImplementedError

    def formatted_header(self):
        """provide the header row """
        return None


class ModelSearchView(SiteSearchView):
    """Reusable search view that search through a Django model"""

    model = get_user_model()
    """searched model """
    searched_attributes = []
    """all attributes that are compared to the pattern """
    sort_attributes = []
    """if provided, results are ordered by these attributes"""

    def get_query(self, request, pattern):
        """compute the query based on the provided pattern and searched attributes"""
        final_query = self.model.objects.all()
        if pattern and self.searched_attributes:
            sub_query = Q(**{self.searched_attributes[0]: pattern})
            for attr in self.searched_attributes[1:]:
                sub_query |= Q(**{attr: pattern})
            final_query = self.model.objects.filter(sub_query)
        if self.sort_attributes:
            final_query = final_query.order_by(*self.sort_attributes)
        return final_query

    def format_result(self, obj):
        """basic format for objects """
        return mark_safe("<td>%s</td>" % obj)


class UserSearchView(ModelSearchView):
    """Search across all users with username and email """

    searched_attributes = ["username__icontains", "email__icontains"]
    """search in usernames and emails """
    sort_attributes = ["last_name", "first_name"]
    """order results by last_name and first_name """

    def format_result(self, obj):
        """a bit better formatted row """
        return mark_safe(
            '<td><a href="%s">%s</a></td><td>%s</td><td>%s</td>'
            % (obj, obj, obj.last_name, obj.first_name)
        )

    def formatted_header(self):
        """headers row """
        return mark_safe("<th>Link</th><th>Name</th><th>First name</th>")
