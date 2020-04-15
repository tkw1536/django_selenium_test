# django-selenium-test

[![Build button](https://travis-ci.com/tkw1536/django_selenium_test.svg?branch=master)](https://travis-ci.com/tkw1536/django_selenium_test/)
![License](https://img.shields.io/pypi/l/django-selenium-test.svg)
![Status](https://img.shields.io/pypi/status/django-selenium-test.svg)
[![Latest version](https://img.shields.io/pypi/v/django-selenium-test.svg)](https://pypi.python.org/pypi/django-selenium-test)

Write Selenium tests on Django 2.x and Python 3.8. 
Based on [django-selenium-clean](https://github.com/aptiko/django-selenium-clean). 

This documentation is currently a work-in-progress. 

## Tutorial

### Installation

In your virtualenv:

```sh
pip install django-selenium-test
```

### Setting up

* Create a new django project and app:

```sh
django-admin startproject foo
cd foo
python manage.py startapp bar
```

* In ``foo/settings.py``, add ``'bar'`` to ``INSTALLED_APPS``

* In ``foo/urls.py``, add ``from bar.views import SimpleView`` to the
  top, and add ``url(r'^$', SimpleView.as_view())`` to ``urlpatterns``.

* Add the SimpleView to ``bar/views.py``:

```python
import textwrap

from django.http import HttpResponse
from django.views.generic.base import View


class SimpleView(View):

    def dispatch(request, *args, **kwargs):
        response_text = textwrap.dedent('''\
            <html>
            <head>
            <title>Greetings to the world</title>
            </head>
            <body>
            <h1 id="earth">Greetings to earth</h1>
            <h1 id="world" style="display: none;">Hello, world!</h1>

            <p>We have some javascript here so that when you click the button
                the heading above toggles between "Greetings to earth" and
                "Hello, world!".</p>

            <button onclick="toggle()">Toggle</button>

            <script type="text/javascript">
                toggle = function () {
                    var heading_earth = document.getElementById("earth");
                    var heading_world = document.getElementById("world");
                    if (heading_earth.style.display == 'none') {
                        heading_world.style.display = 'none';
                        heading_earth.style.display = 'block';
                    } else {
                        heading_earth.style.display = 'none';
                        heading_world.style.display = 'block';
                    }
                }
            </script>
            </body>
            </html>
        ''')
        return HttpResponse(response_text)
```

We're done setting up. If you now run ``python manage.py runserver``
in your browser and visit http://localhost:8000/ in your browser, you
should see the simple page. Let's now proceed to write a test for it.

### Writing the test

Modify ``bar/tests.py`` so that it has the following contents:

```python
from unittest import skipUnless

from django.conf import settings

from django_selenium_test import selenium, SeleniumTestCase, PageElement
from selenium.webdriver.common.by import By


@skipUnless(getattr(settings, 'SELENIUM_WEBDRIVERS', False),
            "Selenium is unconfigured")
class HelloTestCase(SeleniumTestCase):

    heading_earth = PageElement(By.ID, 'earth')
    heading_world = PageElement(By.ID, 'world')
    button = PageElement(By.CSS_SELECTOR, 'button')

    def test_toggle(self):
        # Visit the page
        self.selenium.get(self.live_server_url)

        # Check that the earth heading is visible
        self.assertTrue(self.heading_earth.is_displayed())
        self.assertFalse(self.heading_world.is_displayed())

        # Toggle and check the new condition
        self.button.click()
        self.heading_world.wait_until_is_displayed()
        self.assertFalse(self.heading_earth.is_displayed())
        self.assertTrue(self.heading_world.is_displayed())

        # Toggle again and re-check
        self.button.click()
        self.heading_earth.wait_until_is_displayed()
        self.assertTrue(self.heading_earth.is_displayed())
        self.assertFalse(self.heading_world.is_displayed())
```

### Executing the test

Try ``python manage.py test`` and it will skip the test because
selenium is unconfigured. You need to configure it by specifying
``SELENIUM_WEBDRIVERS`` in ``foo/settings.py``:

```python
from django_selenium_test.settings import make_chrome_driver

SELENIUM_WEBDRIVERS = {
    'default': make_chrome_driver([], {}),
}
```

Now try again, and it should execute the test. 

### Advanced test running tricks

#### Executing a test in many widths

Add this to your ``foo/settings.py``:

```python
SELENIUM_WIDTHS = [1024, 800, 350]
```

This will result in executing all ``SeleniumTestCase``'s three times,
one for each specified browser width. Useful for responsive designs.
The default is to run them on only one width, 1024.

#### Using many selenium drivers

You can have many ``SELENIUM_WEBDRIVERS``:

```python
from django_selenium_test.settings import make_chrome_driver, make_firefox_driver
SELENIUM_WEBDRIVERS = {
    'default': make_chrome_driver([], {})
    'firefox': make_firefox_driver([], {})
}
```

By default, the ``default`` one is used. You can specify another using
the ``SELENIUM_WEBDRIVER`` environment variable:

```sh
SELENIUM_WEBDRIVER=firefox python manage.py test
```


#### Running a headless browser

It can be very useful to run the selenium tests with a headless
browser, that is, in an invisible browser window. For one thing, it
is much faster. 

To achieve this, pass headless=True to the make_BRAND_driver() function:

```python
from django_selenium_test.settings import make_chrome_driver, make_firefox_driver
SELENIUM_WEBDRIVERS = {
    'default': make_chrome_driver([], {}, headless=True)
    'firefox': make_firefox_driver([], {}, headless=True)
}
```

#### Using advanced integration tests

(Currently undocumented)


## Reference

### SeleniumTestCase objects

.. code:: python

   from django_selenium_test import SeleniumTestCase

``SeleniumTestCase`` is the same as Django's
``StaticLiveServerTestCase`` but it adds a little bit of Selenium
functionality. Derive your Selenium tests from this class instead of
``StaticLiveServerTestCase``.

The most important feature of ``SeleniumTestCase`` is the ``selenium``
attribute.  Technically it is a wrapper around the selenium driver. In
practice, you can think about it as the browser, or as the equivalent
of Django's test client. It has all `selenium driver attributes and
methods`_, but you will mostly use ``get()``. It also has the
following additional methods:

* ``self.selenium.login(**credentials)``,
``self.selenium.force_login(user, backend=None)``,
``self.selenium.logout()``

  Similar to the Django test client ``login()``, ``force_login()`` and
  ``logout()`` methods.  ``login()`` returns ``True`` if login is
  possible; ``False`` if the provided credentials are incorrect, or the
  user is inactive, or if the sessions framework is not available.

* ``self.selenium.wait_until_n_windows(n, timeout=2)``

  Useful when a Javascript action has caused the browser to open
  another window. The typical usage is this:

```python
button_that_will_open_a_second_window.click()
self.selenium.wait_until_n_windows(n=2, timeout=10)
windows = self.selenium.window_handles
self.selenium.switch_to_window(windows[1])
# continue testing
```

  If the timeout (in seconds) elapses and the number of browser
  windows never becomes ``n``, an ``AssertionError`` is raised.

.. _selenium driver attributes and methods: http://selenium-python.readthedocs.org/api.html#module-selenium.webdriver.remote.webdriver

PageElement objects
-------------------

```python
from django_selenium_test import PageElement
```

``PageElement`` is a lazy wrapper around WebElement_; it has all its
properties and methods. It is initialized with a locator_, but the
element is not actually located until needed. In addition to
WebElement_ properties and methods, it has these:

* ``PageElement.exists()``: Returns True if the element can be located.

* ``PageElement.wait_until_exists(timeout=10)``

  ``PageElement.wait_until_not_exists(timeout=10)``

  ``PageElement.wait_until_is_displayed(timeout=10)``

  ``PageElement.wait_until_not_displayed(timeout=10)``

  ``PageElement.wait_until_contains(text, timeout=10)``

  ``PageElement.wait_until_not_contains(text, timeout=10)``

  What these methods do should be self-explanatory from their name. The
  ones ending in ``contains`` refer to whether the element contains the
  specified text.  The methods raise an exception if there is a timeout.

- [WebElement](http://selenium-python.readthedocs.org/api.html#module-selenium.webdriver.remote.webelement)
- [locator](http://selenium-python.readthedocs.org/api.html#locate-elements-by)

### IntegrationTest objects
(Currently undocumented)

### Running django-selenium-test's own unit tests

By default the unit tests will use Chrome::

```sh
./setup.py test
```

Use the ``SELENIUM_BROWSER`` environment variable to use another browser:

```sh
SELENIUM_BROWSER=firefox ./setup.py test
```

## License

Licensed under the BSD 3-clause license; see `LICENSE.txt` for details.
