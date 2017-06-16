# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import POD_TEMPLATE_TYPES
from collective.documentgenerator.testing import EXAMPLE_POD_TEMPLATE_INTEGRATION
from collective.documentgenerator.testing import NAKED_PLONE_INTEGRATION

from plone import api

import unittest


class TestInstallDependencies(unittest.TestCase):

    layer = NAKED_PLONE_INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_dexterity_is_dependency_of_documentgenerator(self):
        """
        dexterity should be installed when we install documentgenerator
        """
        dependencies = self.portal.portal_setup.getProfileDependencyChain('collective.documentgenerator:default')
        self.assertTrue(u'profile-plone.app.dexterity:default' in dependencies)

    def test_z3cformdatagridfield_is_dependency_of_documentgenerator(self):
        """
        z3cform.datagridfield should be installed when we install documentgenerator
        """
        dependencies = self.portal.portal_setup.getProfileDependencyChain('collective.documentgenerator:default')
        self.assertTrue(u'profile-collective.z3cform.datagridfield:default' in dependencies)


class TestSetup(unittest.TestCase):

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def test_pod_templates_folder_allowed_types(self):

        portal = api.portal.get()
        pod_folder = portal.podtemplates

        allowed_types = [fti.__name__ for fti in pod_folder.allowedContentTypes()]

        msg = 'pod folder allowed content types should only be the ones from documentgenerator'
        self.assertTrue(len(allowed_types) == len(POD_TEMPLATE_TYPES), msg)
        for portal_type in POD_TEMPLATE_TYPES:
            msg = "type '{}' should be in pod folder allowed types".format(portal_type)
            self.assertTrue(portal_type in allowed_types, msg)
