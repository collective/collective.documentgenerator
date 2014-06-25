# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import IntegrationTestCase

from plone import api


class TestODTTemplate(IntegrationTestCase):
    """
    Test ODTTemplate content type
    """

    def test_ODTTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('ODTTemplate' in registered_types)
