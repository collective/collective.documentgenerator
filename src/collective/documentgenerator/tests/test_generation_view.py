# -*- coding: utf-8 -*-

from AccessControl import Unauthorized

from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.testing import PODTemplateIntegrationTest

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


class TestGenerationViewMethods(PODTemplateIntegrationTest):
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

    def test_document_generation_call(self):
        """
        Check if documents are rendered correctly.
        """
        pod_template = self.test_podtemplate
        test_UID = pod_template.UID()
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('doc_uid', test_UID)
        generated_doc = view()
        # Check if (partial) data of the generated document is the same as the
        # pod_template odt file.
        original_doc = pod_template.get_file()
        self.assertTrue(original_doc.data[1200:2500] in generated_doc)

    def test_unauthorized_generation(self):
        """
        If a template generation condition is not matched, an Unauthorized
        exception should be raised when trying to generate that document.
        """
        pod_template = self.test_podtemplate
        test_UID = pod_template.UID()
        # Make sure can_be_generated will return False.
        pod_template.can_be_generated = lambda x: False
        self.assertTrue(not pod_template.can_be_generated(self.portal))

        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('doc_uid', test_UID)

        unauthorized_raised = False
        try:
            view()
        except Unauthorized:
            unauthorized_raised = True
        self.assertTrue(unauthorized_raised)

    def test_persistent_document_generation_call(self):
        """
        Check if documents are rendered correctly.
        """
        pod_template = self.test_podtemplate
        test_UID = pod_template.UID()
        generation_view = self.portal.restrictedTraverse('@@persistent-document-generation')
        generation_view.request.set('doc_uid', test_UID)
        generation_view()

        msg = "File 'Document A' should have been created on portal."
        self.assertTrue(hasattr(self.portal, 'document-a'), msg)

        persistent_doc = getattr(self.portal, 'document-a')
        generated_doc = persistent_doc.getFile()
        # Check if (partial) data of the generated document is the same as the
        # pod_template odt file.
        original_doc = pod_template.get_file()
        generated = generated_doc.getBlob().open('r').read()
        self.assertTrue(original_doc.data[1200:2500] in generated)

        self.assertTrue(generated_doc.getFilename() == 'Document A.odt')
        self.assertTrue(generated_doc.getContentType() == 'application/vnd.oasis.opendocument.text')

    def test_persistent_document_generation_on_non_folderish_context(self):
        """
        If the generation view is called on a non folderish the document file should be created
        on the parent.
        """
        pod_template = self.test_podtemplate
        test_UID = pod_template.UID()
        non_folderish = api.content.create(type='Document', id='doc', container=self.portal)
        generation_view = non_folderish.restrictedTraverse('@@persistent-document-generation')

        generation_view.request.set('doc_uid', test_UID)
        generation_view()

        msg = "File 'Document A' should have been created on portal."
        self.assertTrue(hasattr(self.portal, 'document-a'), msg)
