# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import POD_TEMPLATE_TYPES
from collective.documentgenerator.interfaces import ICollectiveDocumentGeneratorLayer
from collective.documentgenerator.testing import NAKED_PLONE_INTEGRATION
from collective.documentgenerator.testing import POD_TEMPLATE_INTEGRATION
from plone.browserlayer import utils
from Products.CMFPlone.utils import get_installer

import unittest


class TestInstallDependencies(unittest.TestCase):

    layer = NAKED_PLONE_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_dexterity_is_dependency_of_documentgenerator(self):
        """
        dexterity should be installed when we install documentgenerator
        """
        dependencies = self.portal.portal_setup.getProfileDependencyChain("collective.documentgenerator:default")
        self.assertIn(u"profile-plone.app.dexterity:default", dependencies)

    def test_z3cformdatagridfield_is_dependency_of_documentgenerator(self):
        """
        z3cform.datagridfield should be installed when we install documentgenerator
        """
        dependencies = self.portal.portal_setup.getProfileDependencyChain("collective.documentgenerator:default")
        self.assertIn(u"profile-collective.z3cform.datagridfield:default", dependencies)


class TestSetup(unittest.TestCase):

    layer = POD_TEMPLATE_INTEGRATION

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal)

    def test_pod_templates_folder_allowed_types(self):

        pod_folder = self.portal.podtemplates

        allowed_types = [fti.__name__ for fti in pod_folder.allowedContentTypes()]

        msg = "pod folder allowed content types should only be the ones from documentgenerator"
        self.assertEqual(len(allowed_types), len(POD_TEMPLATE_TYPES), msg)
        for portal_type in POD_TEMPLATE_TYPES:
            msg = "type '{}' should be in pod folder allowed types".format(portal_type)
            self.assertIn(portal_type, allowed_types, msg)

    def test_product_installed(self):
        """Test if collective.documentgenerator is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.is_product_installed("collective.documentgenerator"))

    def test_uninstall(self):
        """Test if collective.documentgenerator is cleanly uninstalled."""
        self.installer.uninstall_product("collective.documentgenerator")
        self.assertFalse(self.installer.is_product_installed("collective.documentgenerator"))

    def test_browserlayer(self):
        """Test that ICollectiveDocumentGeneratorLayer is registered."""
        self.assertIn(ICollectiveDocumentGeneratorLayer, utils.registered_layers())
        self.installer.uninstall_product("collective.documentgenerator")
        self.assertNotIn(ICollectiveDocumentGeneratorLayer, utils.registered_layers())
