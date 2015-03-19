# -*- coding: utf-8 -*-

from Acquisition import aq_base

from collective.documentgenerator.interfaces import IPODTemplateCondition
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.testing import ConfigurablePODTemplateIntegrationTest

from plone import api

from zope.component import queryMultiAdapter

import unittest


class TestConfig(unittest.TestCase):
    """
    Test ConfigurablePODTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_get_uno_path(self):
        from collective.documentgenerator import config
        unopath = config.get_uno_path()
        self.assertTrue(unopath == "/usr/bin/python")

    def test_get_uno_path_with_new_value(self):
        from collective.documentgenerator import config
        newvalue = u"/test"
        unopath = config.get_uno_path()
        self.assertTrue(unopath != newvalue)
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_unoPath',
            newvalue
        )
        unopath = config.get_uno_path()
        self.assertTrue(unopath == newvalue)
