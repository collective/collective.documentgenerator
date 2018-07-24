# -*- coding: utf-8 -*-

from collective.documentgenerator.content.condition import PODTemplateCondition
from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.testing import POD_TEMPLATE_INTEGRATION
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from plone import api
from zope.component import queryMultiAdapter

import unittest


class TestMailingLoopTemplate(unittest.TestCase):
    """
    Test MailingLoopTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_MailingLoopTemplate_portal_type_is_registered(self):
        portal_types = api.portal.get_tool('portal_types')
        registered_types = portal_types.listContentTypes()
        self.assertTrue('MailingLoopTemplate' in registered_types)


class TestMailingLoopTemplateIntegration(unittest.TestCase):
    """
    Test PODTemplate methods.
    """

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(TestMailingLoopTemplateIntegration, self).setUp()
        self.portal = api.portal.get()
        self.test_template = self.portal.podtemplates.get('loop_template')

    def test_default_generation_condition_registration(self):
        context = self.portal
        condition_obj = queryMultiAdapter(
            (self.test_template, context),
            IPODTemplateCondition,
        )

        self.assertTrue(isinstance(condition_obj, PODTemplateCondition))

    def test_default_generation_condition_is_False(self):
        self.assertTrue(self.test_template.can_be_generated(self.portal))
