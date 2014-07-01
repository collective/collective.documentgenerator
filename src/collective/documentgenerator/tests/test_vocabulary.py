# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION

from plone import api

from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestVocabularies(unittest.TestCase):

    layer = TEST_INSTALL_INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']
        self.registry = api.portal.get_tool('portal_registry')

    def test_localities_vocabulary_factory_registration(self):
        """
        Localities voc factory should be registered as a named utility.
        """
        factory_name = 'collective.documentgenerator.Permissions'
        self.assertTrue(queryUtility(IVocabularyFactory, factory_name))

    def test_permissions_vocabulary_values(self):
        """
        Test some permissions values.
        """
        voc_name = 'collective.documentgenerator.Permissions'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        permissions_voc = vocabulary(self.portal)
        self.assertTrue('View' in permissions_voc)
        self.assertTrue('Add portal content' in permissions_voc)
