# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import PODTemplateFunctionalTest
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api

import unittest


class TestConfig(unittest.TestCase):
    """
    Test ConfigurablePODTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_get_oo_port(self):
        from collective.documentgenerator import config
        unopath = config.get_oo_port()
        self.assertTrue(unopath == 2002)

    def test_get_oo_port_with_new_value(self):
        from collective.documentgenerator import config
        newvalue = 4242
        oo_port = config.get_oo_port()
        self.assertTrue(oo_port != newvalue)
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port',
            newvalue
        )
        oo_port = config.get_oo_port()
        self.assertTrue(oo_port == newvalue)

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
            'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path',
            newvalue
        )
        unopath = config.get_uno_path()
        self.assertTrue(unopath == newvalue)


class TestConfigView(PODTemplateFunctionalTest):

    def test_python_path_validator(self):
        """
        """
        self.browser.open('@@collective.documentgenerator-controlpanel')
        form = self.browser.getForm('form')
        pythonpath_input = form.getControl(name="form.widgets.uno_path")
        pythonpath_input.value = 'yolo'
        form.submit('Sauver')
        msg = "pyth path validator should have raised an 'invalid python path' warning"
        self.assertTrue(
            "Le chemin python spécifié semble erroné" in self.browser.contents,
            msg
        )
