# -*- coding: utf-8 -*-

from collective.documentgenerator.content.condition import PODTemplateCondition
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.testing import EXAMPLE_POD_TEMPLATE_INTEGRATION
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api

from zope.component import queryMultiAdapter

import unittest


class TestSubTemplate(unittest.TestCase):
    """
    Test SubTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_SubTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('SubTemplate' in registered_types)


class TestSubTemplateIntegration(unittest.TestCase):
    """
    Test PODTemplate methods.
    """

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(TestSubTemplateIntegration, self).setUp()
        self.portal = api.portal.get()
        self.test_subtemplate = self.portal.podtemplates.get('sub_template')

    def test_default_generation_condition_registration(self):
        context = self.portal
        condition_obj = queryMultiAdapter(
            (self.test_subtemplate, context),
            IPODTemplateCondition,
        )

        self.assertTrue(isinstance(condition_obj, PODTemplateCondition))

    def test_default_generation_condition_is_False(self):
        can_be_generated = self.test_subtemplate.can_be_generated(self.portal)
        self.assertTrue(can_be_generated is False)
