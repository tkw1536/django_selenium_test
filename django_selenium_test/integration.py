from __future__ import annotations

import base64
import time
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select, WebDriverWait

from .core import SeleniumTestCase

if TYPE_CHECKING:
    from typing import Optional, Type, Any, List, Dict, Union, IO
    from django.contrib.auth.models import User
    from django_selenium_clean import SeleniumWrapper
    from selenium.webdriver.remote.webelement import WebElement


class DummyTestBase:
    """ A dummy base class for type-hinting within integration tests """

    selenium: SeleniumWrapper
    live_server_url: str

    def assertTrue(self, expr: bool, msg: Optional[str] = None) -> None:
        ...

    def assertFalse(self, expr: bool, msg: Optional[str] = None) -> None:
        ...

    def assertRaises(
        self, expected_exception: Type[Exception], *args: Any, **kwargs: Any
    ):
        ...

    def assertEqual(self, first: str, second: str, msg: Optional[str] = None) -> None:
        ...


class ElementFindMixins(DummyTestBase):
    find_element_timeout: int
    find_element_selector: str

    def find_element(
        self, selector: str, timeout: Optional[int] = None, clickable: bool = False
    ) -> WebElement:
        """ Finds an element by a selector and waits for it to become available """

        if timeout is None:
            timeout = self.__class__.find_element_timeout
        if selector is None:
            selector = self.__class__.find_element_selector

        wait = WebDriverWait(self.selenium, timeout)

        if clickable:
            condition = expected_conditions.element_to_be_clickable
        else:
            condition = expected_conditions.visibility_of_element_located

        return wait.until(condition((By.CSS_SELECTOR, selector)))

    def find_next_sibling(self, element: WebElement) -> Optional[WebElement]:
        """ Finds the next sibling of an element """
        return self.selenium.execute_script(
            "return arguments[0].nextElementSibling; ", element
        )


class ElementAssertionMixins(DummyTestBase):
    def _element_exists(self, selector: str) -> bool:
        """ Checks if an element with the given selector exists on the page """
        return len(self.selenium.find_elements(By.CSS_SELECTOR, selector)) > 0

    def _element_displayed(self, selector: str) -> bool:
        """ Checks if an element with a given selector exists and is displayed """

        for element in self.selenium.find_elements(By.CSS_SELECTOR, selector):
            return element.is_displayed()
        return False

    def assert_element_exists(self, selector: str, *args: Any) -> None:
        """ Asserts that an element exists on the current page """
        return self.assertTrue(self._element_exists(selector), *args)

    def assert_element_not_exists(self, selector: str, *args: Any) -> None:
        """ Asserts that an element does not exist on the current page """
        return self.assertFalse(self._element_exists(selector), *args)

    def assert_element_displayed(self, selector: str, *args: Any) -> None:
        """ Asserts that an element with the given selector is displayed """
        return self.assertTrue(self._element_displayed(selector), *args)

    def assert_element_not_displayed(self, selector: str, *args: Any) -> None:
        """ Asserts that an element with the given selector is not displayed """
        return self.assertFalse(self._element_displayed(selector), *args)


class FormElementMixins(DummyTestBase):
    def fill_out_form(
        self,
        url_pattern: str,
        submit_button: str = None,
        send_form_keys: Optional[Dict[str, str]] = None,
        select_dropdowns: Optional[Dict[str, str]] = None,
        select_checkboxes: Optional[Dict[str, bool]] = None,
        script_value: Optional[Dict[str, str]] = None,
        selector: Optional[str] = None,
        url_args: Optional[List[str]] = None,
        url_kwargs: Optional[Dict[str, Any]] = None,
        url_reverse_get_params: Optional[Dict[str, Any]] = None,
        selector_timeout: Optional[int] = None,
    ) -> WebElement:
        """
            Loads a URL using selenium from the live server and waits for the element with the submit_button id to be
            available.
            Once available, uses send_keys to send strings to elements with ids as specificed by send_form_keys dict.
            Next, selects either one item by visible text, or muliple items by value, in dropdowns specified by the
            select_dropdowns element.
            Next, sets the selection state of checkboxes of elements with ids as specified by the select_checkboxes
            dict.
            Next, directly set the value attribute of elements refered to by the script_value dict.
            Finally returns the button element.
        """
        if submit_button is None:
            selector = None
        else:
            selector = "#{}".format(submit_button)

        # get the element on the page
        button = self.load_live_url(
            url_pattern,
            selector=selector,
            url_args=url_args,
            url_kwargs=url_kwargs,
            url_reverse_get_params=url_reverse_get_params,
            selector_timeout=selector_timeout,
            selector_clickable=True,
        )

        # send_keys to the specified form elements
        if send_form_keys is not None:
            for id_, value in send_form_keys.items():
                element = self.selenium.find_element_by_id(id_)
                element.clear()
                element.send_keys(value)

        # select inside the specified dropdowns
        if select_dropdowns is not None:
            for id_, value in select_dropdowns.items():
                self.select_dropdown(id_, value)

        # select the checkboxes
        if select_checkboxes is not None:
            for id_, value in select_checkboxes.items():
                checkbox = self.selenium.find_element_by_id(id_)
                if checkbox.is_selected() != value:
                    checkbox.click()

        # set the scripted values
        if script_value is not None:
            for id_, value in script_value.items():
                element = self.selenium.find_element_by_id(id_)
                self.selenium.execute_script(
                    "arguments[0].value = arguments[1];", element, value
                )

        # return the button
        return button

    def submit_form(
        self,
        *args: Any,
        next_selector: Optional[str] = None,
        selector_timeout: Optional[int] = None,
        **kwargs: Any
    ) -> WebElement:
        """ Fills out and submit a form, then returns the body element of the submitted page """

        # fill out the form and click the submit button
        button = self.fill_out_form(*args, selector_timeout=selector_timeout, **kwargs)
        button.click()

        # wait for next element to be visible
        return self.find_element(next_selector, timeout=selector_timeout)

    def disable_form_requirements(self) -> None:
        self.selenium.execute_script(
            """
        var inputs = document.getElementsByTagName('input');
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].removeAttribute('required');
        }
        var selects = document.getElementsByTagName('select');
        for (var i = 0; i < selects.length; i++) {
            selects[i].removeAttribute('required');
        }
        """
        )

    def get_form_download(self, form: WebElement) -> [bool, IO[bytes]]:
        """ Virtually submits a form and intercepts the resulting downloaded file as a BytesIO """
        self.selenium.execute_script(
            """
        window.xhr_done = false;
        window.xhr_ok = null;
        window.xhr_data = null;

        function create_form_xhr(form) {
            const xhr = new XMLHttpRequest();
            setup_xhr_handler(xhr);
            const fd = new FormData(form);
            xhr.open('POST', form.getAttribute('action') || window.location.href);
            xhr.send(fd);
            return xhr;
        }
        function setup_xhr_handler(xhr) {
            xhr.responseType = 'blob';
            xhr.onload = function() {
                const reader  = new FileReader();
                reader.onloadend = function() {
                    window.xhr_data = reader.result;
                    window.xhr_ok = xhr.status === 200;
                    window.xhr_done = true;
                };
                reader.readAsDataURL(xhr.response);
            };
        }
        create_form_xhr(arguments[0].form);
        """,
            form,
        )

        xhr_done = False
        while xhr_done == False:
            xhr_done = self.selenium.execute_script("return window.xhr_done;")
            time.sleep(0.1)

        xhr_ok = self.selenium.execute_script("return window.xhr_ok;")
        xhr_data = self.selenium.execute_script("return window.xhr_data; ")

        # if there is some data, return it
        if xhr_data is not None:
            xhr_data = xhr_data.split(",")[1]
            xhr_data = base64.b64decode(xhr_data)

        return xhr_ok, xhr_data

    def hover_element(self, id_: str) -> WebElement:
        """ Hovers over an element with the given ID """
        element = self.selenium.find_element_by_id(id_)

        hover = ActionChains(self.selenium).move_to_element(element)
        hover.perform()

        return element

    def select_dropdown(
        self, id_or_element: Union[str, WebElement], value: str
    ) -> Select:
        """ Selects text of a dropdown by value """

        # if we don't have an element, select it by selector
        if isinstance(id_or_element, str):
            id_or_element = self.selenium.find_element_by_id(id_or_element)

        select = Select(id_or_element)

        # if we are a multiple select, deselect all of them
        if select.is_multiple:
            select.deselect_all()

        # if the value was set to none, do nothing
        if value is None:
            return select

        # if we have a string, select by visible text
        if isinstance(value, str):
            select.select_by_visible_text(value)

        # else select all the ones by the given value
        else:
            for v in value:
                select.select_by_value(v)

        return select


class URLMixins(DummyTestBase):
    def _resolve_url(
        self,
        url: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        get_params: Option[Dict[str, str]] = None,
        reverse_get_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """ Resolves a url pattern into an actual url """

        # If it's an absolute url, the test case is wrong
        if url.startswith("/"):
            raise AssertionError(
                "_resolve_url() does not accept absolute urls, got: {}".format(url)
            )

        # the url itself is resolved using 'reverse'
        resolved = reverse(url, args=args, kwargs=kwargs)

        # extra get parameters
        extra_args = {}
        has_extra_args = False

        # extra url params
        if get_params is not None:
            has_extra_args = True
            extra_args.update(get_params)

        # reversed get params
        if reverse_get_params is not None:
            has_extra_args = True
            for (k, v) in reverse_get_params.items():
                extra_args[k] = reverse(v)

        # if we had some extra arguments
        if has_extra_args:
            resolved = (
                resolved
                + "?"
                + "&".join(["{}={}".format(k, v) for (k, v) in extra_args.items()])
            )

        # and return the resolved url
        return resolved

    @property
    def _current_url(self) -> str:
        """ The current url of the server relative to the root """

        url = str(self.selenium.current_url)
        if url.startswith(self.live_server_url):
            return url[len(self.live_server_url) :]
        return url

    def load_live_url(
        self,
        url_pattern: str,
        selector: str = None,
        url_args: Optional[List[Any]] = None,
        url_kwargs: Optional[Dict[str, Any]] = None,
        url_get_params: Option[Dict[str, str]] = None,
        url_reverse_get_params: Optional[Dict[str, Any]] = None,
        selector_timeout: Optional[int] = None,
        selector_clickable: bool = False,
    ) -> WebElement:
        """
            Loads an url from the selenium from the live server and waits for the CSS selector (if any) to be available
            Returns the element selected, None if none is selected, or raises TimeoutException if a timeout occurs.
        """

        # resolve the url and load it
        url = self._resolve_url(
            url_pattern,
            args=url_args,
            kwargs=url_kwargs,
            get_params=url_get_params,
            reverse_get_params=url_reverse_get_params,
        )
        self.selenium.get(self.live_server_url + url)

        # wait for the element
        return self.find_element(
            selector, timeout=selector_timeout, clickable=selector_clickable
        )

    def assert_url_equal(self, url: str, *args: Any, **kwargs: Any) -> None:
        """ Asserts that the current url is equal to the (pontially resolvable) url """

        got = self._current_url
        expected = self._resolve_url(url, **kwargs)
        return self.assertEqual(got, expected, *args)

    def assert_url_follow(
        self,
        url: str,
        new_url: str,
        *args,
        url_args=None,
        url_kwargs=None,
        url_reverse_get_params=None,
        new_url_args=None,
        new_url_kwargs=None,
        new_url_reverse_get_params=None,
        url_selector: str = None,
        url_selector_timeout: int = None
    ):
        """
            Asserts that loading url (with selector selector) in the browser redirects to new_url. 
        """

        # load the url
        self.load_live_url(
            url,
            url_args=url_args,
            url_kwargs=url_kwargs,
            url_reverse_get_params=url_reverse_get_params,
            selector=url_selector,
            selector_timeout=url_selector_timeout,
        )

        # and check that it's equal
        return self.assert_url_equal(
            new_url,
            args=new_url_args,
            kwargs=new_url_kwargs,
            reverse_get_params=new_url_reverse_get_params,
            *args
        )


class IntegrationTestBase(
    ElementAssertionMixins,
    ElementFindMixins,
    FormElementMixins,
    URLMixins,
    DummyTestBase,
):
    """ A base class for integration tests """

    user: Optional[User] = None
    selenium: SeleniumWrapper = None
    live_server_url: str = None

    find_element_timeout: int = 10
    find_element_selector = None  # to be overwritten by subclass

    def login(self, username: str) -> User:
        """ Authenticates the user with the given username and returns the user object """

        # grab the instance of the user we want to login
        user = get_user_model().objects.get(username=username)

        # and force the login
        self.selenium.force_login(user)

        # return the user
        return user


class IntegrationTest(SeleniumTestCase, IntegrationTestBase):
    """ An integration test base class using Selenium """

    def setUp(self) -> None:
        """ Setups up this test class """

        # before each test case, we need to reset the cookies
        self.selenium.delete_all_cookies()

        user = self.__class__.user
        if user is not None:
            self.user = self.login(user)  # type: User
