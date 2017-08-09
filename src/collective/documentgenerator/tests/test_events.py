# -*- coding: utf-8 -*-

from collective.documentgenerator.events.styles_events import _update_template_styles
from collective.documentgenerator.events.styles_events import update_styles_of_all_PODtemplate
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from zExceptions import Redirect


class TestEvents(PODTemplateIntegrationTest):
    """
    Test events methods.
    """

    def test_update_styles_of_all_PODtemplate(self):
        # we use a ConfigurablePODTemplate to test style modification
        style_template = self.portal.podtemplates.get('test_style_template')
        # just call the function to pass on code
        update_styles_of_all_PODtemplate(style_template, None)

    def test__update_template_styles(self):
        # style update is already tested in test_utils.py
        # this is done to check error management
        template = self.portal.podtemplates.get('test_template_multiple')
        self.assertRaises(Redirect, _update_template_styles, template, None)
