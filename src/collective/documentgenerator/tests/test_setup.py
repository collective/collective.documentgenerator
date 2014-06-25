# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import NAKED_PLONE_INTEGRATION

from plone import api
from plone.app.testing import applyProfile

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
        self.assertTrue(not self.installer.isProductInstalled('plone.app.dexterity'))
        applyProfile(self.portal, 'collective.documentgenerator:testing')
        self.assertTrue(self.installer.isProductInstalled('plone.app.dexterity'))
