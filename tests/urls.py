from __future__ import annotations

from django.urls import path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from .views import DownloadView, SampleFormView

urlpatterns = [
    path("core/", TemplateView.as_view(template_name="core.html"), name="core"),
    # lots of urls for the integration test
    path(r"integration/", SampleFormView.as_view(), name="integration"),
    path(
        r"integration/submit/",
        TemplateView.as_view(template_name="integration.html"),
        name="integrationsubmit",
    ),
    path(
        r"integration/parameter/<int:parameter>/",
        TemplateView.as_view(template_name="integration.html"),
        name="integrationparams",
    ),
    path(
        r"integration/redirect/",
        RedirectView.as_view(pattern_name="integration"),
        name="integrationredirect",
    ),
    path(r"integration/file/", DownloadView.as_view(), name="integrationdownload"),
]
