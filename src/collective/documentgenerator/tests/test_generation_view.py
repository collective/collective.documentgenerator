# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.testing import PODTemplateIntegrationBrowserTest

from plone import api

import unittest


class TestGenerationView(unittest.TestCase):
    """
    Test document generation view.
    """

    layer = TEST_INSTALL_INTEGRATION

    def test_view_registration(self):
        from collective.documentgenerator.browser.generation_view import DocumentGenerationView

        portal = api.portal.getSite()
        generation_view = portal.restrictedTraverse('@@document-generation')
        self.assertTrue(generation_view)
        self.assertTrue(isinstance(generation_view, DocumentGenerationView))


class TestGenerationViewMethods(PODTemplateIntegrationBrowserTest):
    """
    """

    def test_get_pod_template_uid(self):
        test_UID = '12345'
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('doc_uid', test_UID)
        msg = 'get_pod_template_uid() should return UID \'{}\''.format(test_UID)
        self.assertTrue(view.get_pod_template_uid() == test_UID, msg)
