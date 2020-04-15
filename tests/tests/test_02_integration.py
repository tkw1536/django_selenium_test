from __future__ import annotations

from unittest import mock

from django_selenium_test import IntegrationTest


class ExampleIntegrationTest(IntegrationTest):

    find_element_selector = "main"

    def test_element_mixins(self) -> None:
        """ Checks that the element mixins work as intended """

        self.load_live_url("integration")

        test_element = self.find_element("#test")
        self.assertIsNotNone(test_element, "Can find the test element")

        test_next_element = self.find_element("#test_next")
        self.assertIsNotNone(test_next_element, "Can find the test next element")

        self.assertEqual(
            self.find_next_sibling(test_element),
            test_next_element,
            "Checks that find_next_sibling works as expected",
        )

    def test_element_assertions(self) -> None:
        """ Checks that the element assertions work as intended """

        self.load_live_url("integration")

        self.assert_element_exists("#exists")
        self.assert_element_not_exists("#not_exists")

        self.assert_element_displayed("#displayed")
        self.assert_element_not_displayed("#not_displayed")
        self.assert_element_not_displayed("#not_exists")

    def test_urls(self) -> None:

        # check that load_live_url and assert_url_equal work
        self.load_live_url(
            "integrationparams",
            url_kwargs={"parameter": 12},
            url_reverse_get_params={"next": "integration"},
        )
        self.assert_url_equal(
            "integrationparams",
            kwargs={"parameter": 12},
            reverse_get_params={"next": "integration"},
        )

        # check that the follow function works
        self.assert_url_follow("integrationredirect", "integration")

    @mock.patch("tests.views.cleaned_data_check", return_value=1)
    def test_fill_form(self, cmock: mock.Mock) -> None:

        # fill in the form normally
        self.submit_form(
            "integration",
            "input_id_submit",
            send_form_keys={"id_a": "Filled in A"},
            select_dropdowns={"id_b": "b"},
            script_value={"id_c": "Filled in C"},
        )
        self.assert_url_equal("integrationsubmit")
        cmock.assert_has_calls(
            [mock.call({"a": "Filled in A", "b": "b", "c": "Filled in C"})]
        )

        # fill in the form, but set b manually
        cmock.reset_mock()
        submit = self.fill_out_form(
            "integration",
            "input_id_submit",
            send_form_keys={"id_a": "Filled in A"},
            select_dropdowns={"id_b": "a"},
            script_value={"id_c": "Filled in C"},
        )
        self.select_dropdown(self.find_element("#id_b"), "b")
        submit.click()
        self.assert_url_equal("integrationsubmit")
        cmock.assert_has_calls(
            [mock.call({"a": "Filled in A", "b": "b", "c": "Filled in C"})]
        )

        # reset all the things
        cmock.reset_mock()
        submit = self.fill_out_form(
            "integration",
            "input_id_submit",
            send_form_keys={"id_a": "Filled in A"},
            select_dropdowns={"id_b": "b"},
        )

        # hack away the required fields, and then submit
        self.disable_form_requirements()
        submit.click()

        # check that the submission failed
        self.assert_url_equal("integration")
        cmock.assert_not_called()

        # submitting a download form and getting the content
        ok, data = self.get_form_download(self.find_element("#input_id_download"))
        self.assertEqual(ok, True)
        self.assertEqual(data, b"content of example.txt")

        # hover an element
        self.hover_element("hoverable")
        self.assertEqual(
            self.find_element("#hoverable").get_attribute("data-hovered"), "true"
        )
