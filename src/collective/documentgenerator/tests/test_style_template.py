# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api

from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import unittest


class TestStyleTemplate(unittest.TestCase):
    """
    Test StyleTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_StyleTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('StyleTemplate' in registered_types)


class TestStyleTemplateUpdate(ConfigurablePODTemplateIntegrationTest):
    """
    """

    style_template = self.portal.podtemplates.test_style_template_2
