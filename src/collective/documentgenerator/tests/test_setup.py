# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from collective.documentgenerator.testing import IntegrationTestCase
from plone import api


class TestInstall(IntegrationTestCase):
    """Test installation of collective.documentgenerator into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if collective.documentgenerator is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('collective.documentgenerator'))

    def test_uninstall(self):
        """Test if collective.documentgenerator is cleanly uninstalled."""
        self.installer.uninstallProducts(['collective.documentgenerator'])
        self.assertFalse(self.installer.isProductInstalled('collective.documentgenerator'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that ICollectiveDocumentgeneratorLayer is registered."""
        from collective.documentgenerator.interfaces import ICollectiveDocumentgeneratorLayer
        from plone.browserlayer import utils
        self.assertIn(ICollectiveDocumentgeneratorLayer, utils.registered_layers())
