import os
from tempfile import NamedTemporaryFile

from selenium import webdriver

from django_selenium_test.settings import make_chrome_driver, make_firefox_driver

DEBUG = False

ROOT_URLCONF = "tests.urls"

SECRET_KEY = "topsecret"

ALLOWED_HOSTS = ["*"]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": NamedTemporaryFile().name,
    }
}

STATIC_URL = "/static/"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(os.path.dirname(__file__), "templates")],
        "OPTIONS": {
            "context_processors": ["django.template.context_processors.request"]
        },
    }
]


headless = os.environ.get("SELENIUM_HEADLESS") != "0"
SELENIUM_WEBDRIVERS = {
    "default": make_chrome_driver([], {}, headless=headless),
    "chrome": make_chrome_driver([], {}, headless=headless),
    "firefox": make_firefox_driver([], {}, headless=headless),
}
