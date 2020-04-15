from __future__ import absolute_import, annotations

import os
import signal
import time
from importlib import import_module
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.http import HttpRequest

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

if TYPE_CHECKING:
    from typing import Optional, Any
    from selenium.webdriver.remote.webdriver import WebDriver
    from django.contrib.auth.models import AbstractUser


class SeleniumWrapper(object):
    _instance = None
    driver: WebDriver

    def __new__(cls, *args: Any, **kwargs: Any) -> SeleniumWrapper:
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        SELENIUM_WEBDRIVERS = getattr(settings, "SELENIUM_WEBDRIVERS", {})
        if not SELENIUM_WEBDRIVERS:
            return
        driver_id = os.environ.get("SELENIUM_WEBDRIVER", "default")
        driver = SELENIUM_WEBDRIVERS[driver_id]
        callable = driver["callable"]
        args = driver["args"]
        kwargs = driver["kwargs"]
        self.driver = callable(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.driver, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "driver":
            super(SeleniumWrapper, self).__setattr__(name, value)
        else:
            setattr(self.driver, name, value)

    def __bool__(self) -> bool:
        return bool(self.driver)

    __nonzero__ = __bool__  # Python 2 compatibility

    def login(self, **credentials: Any) -> bool:
        """
        Sets selenium to appear as if a user has successfully signed in.

        Returns True if signin is possible; False if the provided
        credentials are incorrect, or the user is inactive, or if the
        sessions framework is not available.

        The code is based on django.test.client.Client.login.
        """
        from django.contrib.auth import authenticate

        user = authenticate(**credentials)
        if (
            user
            and user.is_active
            and "django.contrib.sessions" in settings.INSTALLED_APPS
        ):
            self._login(user)
            return True
        else:
            return False

    def force_login(self, user: AbstractUser, base_url: str) -> None:
        """
        Sets selenium to appear as if a user has successfully signed in.

        The user will have its backend attribute set to the value of the
        backend argument (which should be a dotted Python path string),
        or to settings.AUTHENTICATION_BACKENDS[0] if a value isn't
        provided. The authenticate() function called by login() normally
        annotates the user like this.

        The code is based on https://github.com/feffe/django-selenium-login/blob/master/seleniumlogin/__init__.py. 
        """

        # The original code was licensed under:
        #
        #
        # MIT License
        #
        # Copyright (c) 2016 Fredrik Westermark
        #
        # Permission is hereby granted, free of charge, to any person obtaining a copy
        # of this software and associated documentation files (the "Software"), to deal
        # in the Software without restriction, including without limitation the rights
        # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        # copies of the Software, and to permit persons to whom the Software is
        # furnished to do so, subject to the following conditions:
        #
        # The above copyright notice and this permission notice shall be included in all
        # copies or substantial portions of the Software.
        #
        # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        # SOFTWARE.
        #
        from django.conf import settings

        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        selenium_login_start_page = getattr(
            settings, "SELENIUM_LOGIN_START_PAGE", "/page_404/"
        )
        self.driver.get("{}{}".format(base_url, selenium_login_start_page))

        session = SessionStore()
        session[SESSION_KEY] = user.id
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        cookie = {
            "name": settings.SESSION_COOKIE_NAME,
            "value": session.session_key,
            "path": "/",
        }
        self.driver.add_cookie(cookie)
        self.driver.refresh()

    def _login(self, user: AbstractUser, backend: Optional[str] = None) -> None:
        from django.contrib.auth import login

        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        request.session = engine.SessionStore()
        login(request, user, backend)

        # Save the session values.
        request.session.save()

        # Set the cookie to represent the session.
        cookie_data = {
            "name": settings.SESSION_COOKIE_NAME,
            "value": request.session.session_key,
            "max-age": None,
            "path": "/",
            "secure": settings.SESSION_COOKIE_SECURE or False,
            "expires": None,
        }
        self.add_cookie(cookie_data)

        return True

    def logout(self) -> None:
        """
        Removes the authenticated user's cookies and session object.

        Causes the authenticated user to be logged out.
        """
        session = import_module(settings.SESSION_ENGINE).SessionStore()
        session_cookie = self.get_cookie(settings.SESSION_COOKIE_NAME)
        if session_cookie:
            session.delete(session_key=session_cookie["value"])
            self.delete_cookie(settings.SESSION_COOKIE_NAME)

    def wait_until_n_windows(self, n: int, timeout: int = 2) -> None:
        for i in range(timeout * 10):
            if len(self.window_handles) == n:
                return
            time.sleep(0.1)
        raise AssertionError("Timeout while waiting for {0} windows".format(n))

    def quit(self) -> None:
        # The way to exit the browser is selenium.driver.quit(), however we
        # exit PhantomJS differently because of
        # https://github.com/SeleniumHQ/selenium/issues/767
        if self.driver.capabilities["browserName"] == "phantomjs":
            self.driver.service.process.send_signal(signal.SIGTERM)
        else:
            self.driver.quit()


class SeleniumTestCase(StaticLiveServerTestCase):
    selenium: SeleniumWrapper

    @classmethod
    def setUpClass(cls) -> None:

        super(SeleniumTestCase, cls).setUpClass()
        cls.selenium = SeleniumWrapper()
        PageElement.selenium = cls.selenium

        # Normally we would just do something like
        #     selenium.live_server_url = self.live_server_url
        # However, there is no "self" at this time, so we
        # essentially duplicate the code from the definition of
        # the LiveServerTestCase.live_server_url property.
        cls.selenium.live_server_url = "http://%s:%s" % (
            cls.server_thread.host,
            cls.server_thread.port,
        )

    @classmethod
    def tearDownClass(cls) -> None:

        cls.selenium.quit()
        PageElement.selenium = None
        super().tearDownClass()

    def __call__(self, result=None):
        if hasattr(self, "selenium"):
            for width in getattr(settings, "SELENIUM_WIDTHS", [1024]):
                self.selenium.set_window_size(width, 1024)
        return super().__call__(result)


class PageElement(object):

    selenium: Optional[WebDriver] = None

    def __init__(self, *args: Any) -> None:
        if len(args) == 2:
            self.locator = args

    def wait_until_exists(self, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until(
            EC.presence_of_element_located(self.locator)
        )

    def wait_until_not_exists(self, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until_not(
            EC.presence_of_element_located(self.locator)
        )

    def wait_until_is_displayed(self, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until(
            EC.visibility_of_element_located(self.locator)
        )

    def wait_until_not_displayed(self, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until_not(
            EC.visibility_of_element_located(self.locator)
        )

    def wait_until_contains(self, text: str, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until(
            EC.text_to_be_present_in_element(self.locator, text)
        )

    def wait_until_not_contains(self, text: str, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until_not(
            EC.text_to_be_present_in_element(self.locator, text)
        )

    def wait_until_is_clickable(self, timeout: int = 10) -> None:
        WebDriverWait(self.selenium, timeout).until(
            EC.element_to_be_clickable(self.locator)
        )

    def exists(self) -> bool:
        return len(self.selenium.find_elements(*self.locator)) > 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self.selenium.find_element(*self.locator), name)
