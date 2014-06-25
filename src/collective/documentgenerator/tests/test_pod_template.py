# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import IntegrationTestCase

from plone import api


class TestPODTemplate(IntegrationTestCase):
    """
    Test PODTemplate content type
    """

    def test_PODTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('PODTemplate' in registered_types)
