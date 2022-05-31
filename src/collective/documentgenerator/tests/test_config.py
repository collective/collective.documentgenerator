# -*- coding: utf-8 -*-
from collective.documentgenerator.testing import PODTemplateFunctionalTest
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from plone import api

import os
import unittest


class TestConfig(unittest.TestCase):
    """
    Test ConfigurablePODTemplate content type.
    """

    layer = TEST_INSTALL_INTEGRATION

    def tearDown(self):
        # reset oo_port to 2002 after each test
        os.environ['OO_PORT'] = '2002'
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port_list',
            u'2002'
        )

    def test_get_oo_port_list(self):
        from collective.documentgenerator import config
        oo_port_list = config.get_oo_port_list()
        self.assertTrue(oo_port_list == [2002])

    def test_get_oo_port_with_new_values(self):
        from collective.documentgenerator import config
        newvalues = [4242, 6666]
        oo_ports = config.get_oo_port_list()
        self.assertTrue(newvalues != oo_ports)
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.oo_port_list',
            u';'.join([unicode(v) for v in newvalues])
        )
        oo_port = config.get_oo_port_list()
        self.assertTrue(oo_port == newvalues)

    def test_get_uno_path(self):
        from collective.documentgenerator import config
        unopath = config.get_uno_path()
        self.assertTrue(unopath[:15] == '/usr/bin/python')

    def test_get_uno_path_with_new_value(self):
        from collective.documentgenerator import config
        newvalue = u'/test'
        unopath = config.get_uno_path()
        self.assertTrue(unopath != newvalue)
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.uno_path',
            newvalue
        )
        unopath = config.get_uno_path()
        self.assertTrue(unopath == newvalue)

    def test_set_oo_port(self):
        from collective.documentgenerator import config
        self.assertEqual(config.get_oo_port_list(), [2002])
        config.set_oo_port()
        self.assertEqual(config.get_oo_port_list(), [2002])
        os.environ['OO_PORT'] = '6969'
        config.set_oo_port()
        self.assertEqual(config.get_oo_port_list(), [6969])


class TestConfigView(PODTemplateFunctionalTest):
    """
    Test documentgenerator controlpanel view.
    """

    def _open_controlpanel(self):
        self.browser.open('{}/@@collective.documentgenerator-controlpanel'.format(self.portal.absolute_url()))

    def setUp(self):
        super(TestConfigView, self).setUp()
        self._open_controlpanel()
        self.form = self.browser.getForm('form')

    def test_python_path_validator(self):
        pythonpath_input = self.form.getControl(name='form.widgets.uno_path')
        pythonpath_input.value = 'yolo'
        self.form.submit(name='form.buttons.save')
        msg = "python path validator should have raised an 'invalid python path' warning"
        self.assertTrue(
            'Le chemin python spécifié semble erroné' in self.browser.contents,
            msg
        )

    def test_python_with_uno_validator(self):
        pythonpath_input = self.form.getControl(name='form.widgets.uno_path')
        pythonpath_input.value = os.path.abspath('../../bin/python')
        self.form.submit(name='form.buttons.save')
        msg = "python path validator should have raised an 'python do not have uno library' warning"
        self.assertTrue(
            "L'importation de la librairie UNO dans votre environnement python a échoué" in self.browser.contents,
            msg
        )

    def test_cancel_button(self):
        self.form.submit('Annuler')
        msg = 'We should have gone back on general control panel view'
        control_panel_url = self.browser.getLink('Configuration du site').url
        self.assertTrue(self.browser.url == control_panel_url, msg)
