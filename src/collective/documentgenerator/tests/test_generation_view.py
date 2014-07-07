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
        """
        By default, the template uid to generate should be in the argument
        'doc_uid' of the request.
        """
        test_UID = '12345'
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('doc_uid', test_UID)
        msg = 'get_pod_template_uid() should return UID \'{}\''.format(test_UID)
        self.assertTrue(view.get_pod_template_uid() == test_UID, msg)

    def test_get_pod_template(self):
        """
        When passing a real template UID, get_pod_template() should return this
        template.
        """
        pod_template = self.test_podtemplate
        test_UID = pod_template.UID()
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('doc_uid', test_UID)
        self.assertTrue(view.get_pod_template() == pod_template)

    def test_get_pod_template_not_found(self):
        """
        When a template cannot be found, a PODTemplateNotFoundError should be raised.
        """
        from collective.documentgenerator.interfaces import PODTemplateNotFoundError

        test_UID = 'TROLOLO'
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('doc_uid', test_UID)
        error_raised = False
        try:
            view.get_pod_template()
        except PODTemplateNotFoundError:
            error_raised = True
        self.assertTrue(error_raised)
