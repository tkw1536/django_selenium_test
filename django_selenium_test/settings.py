from __future__ import annotations

from typing import TYPE_CHECKING

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

if TYPE_CHECKING:
    from typing import List, Dict, Any


def make_chrome_driver(
    args: List[Any], kwargs: Dict[str, Any], headless=False
) -> Dict[str, Any]:
    """ Makes a new chrome driver settings instance """
    kwargs.update({"options": _make_chrome_options(headless)})

    return {
        "callable": webdriver.Chrome,
        "args": args,
        "kwargs": kwargs,
    }


def _make_chrome_options(headless: bool) -> ChromeOptions:
    """ Creates a new options instance for the chrome webdriver """
    chrome_options = ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless")
    return chrome_options


def make_firefox_driver(
    args: List[Any], kwargs: Dict[str, Any], headless=False
) -> Dict[str, Any]:
    """ Makes a new chrome driver settings instance """
    kwargs.update({"options": _make_firefox_options(headless)})

    return {
        "callable": webdriver.Firefox,
        "args": args,
        "kwargs": kwargs,
    }


def _make_firefox_options(headless: bool) -> FirefoxOptions:
    """ Creates a new options instance for the firefox webdriver """
    firefox_options = FirefoxOptions()
    if headless:
        firefox_options.add_argument("--headless")
    return firefox_options
