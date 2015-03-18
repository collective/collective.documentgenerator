# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api

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
