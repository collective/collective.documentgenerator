# -*- coding: utf-8 -*-

from AccessControl import Unauthorized

from collective.documentgenerator.interfaces import CyclicMergeTemplatesException
from collective.documentgenerator.interfaces import PODTemplateNotFoundError
from collective.documentgenerator.testing import EXAMPLE_POD_TEMPLATE_INTEGRATION
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
        By default, this will get the 'template_uid' from the request.
        """
        test_UID = '12345'
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('template_uid', test_UID)
        self.assertTrue(view.get_pod_template_uid() == test_UID)

    def test_get_generation_format(self):
        """
        By default, this will get the 'output_format' from the request.
        """
        output_format = 'odt'
        view = self.portal.restrictedTraverse('@@document-generation')
        view.request.set('output_format', output_format)
        self.assertTrue(view.get_generation_format() == output_format)

    def test__call__params_not_given(self):
        """
        __call__ receives 'template_uid' and 'output_format' as params, if it is None,
        it tries to get it using 'get_pod_template_uid' and 'get_generation_format' methods.
        """
        pod_template = self.test_podtemplate
        template_uid = pod_template.UID()
        view = self.portal.podtemplates.restrictedTraverse('@@document-generation')
        self.assertRaises(PODTemplateNotFoundError, view, template_uid=None, output_format=None)
        # set parameters in REQUEST as it is default implementation of
        # 'get_pod_template_uid' and 'get_generation_format' methods
        view.request.set('template_uid', template_uid)
        view.request.set('output_format', 'odt')
        self.assertTrue(view())

    def test_get_pod_template(self):
        """
        When passing a real template UID, get_pod_template() should return this
        template.
        """
        pod_template = self.test_podtemplate
        template_uid = pod_template.UID()
        view = self.portal.restrictedTraverse('@@document-generation')
        self.assertTrue(view.get_pod_template(template_uid) == pod_template)

    def test_get_pod_template_not_found(self):
        """
        When a template cannot be found, a PODTemplateNotFoundError should be raised.
        """
        from collective.documentgenerator.interfaces import PODTemplateNotFoundError

        template_uid = 'TROLOLO'
        view = self.portal.restrictedTraverse('@@document-generation')
        error_raised = False
        try:
            view.get_pod_template(template_uid)
        except PODTemplateNotFoundError:
            error_raised = True
        self.assertTrue(error_raised)

    def test_document_generation_call(self):
        """
        Check if documents are rendered correctly.
        """
        pod_template = self.test_podtemplate
        template_uid = pod_template.UID()
        view = self.portal.podtemplates.restrictedTraverse('@@document-generation')
        # an 'output_format' must be given or it raises an Exception
        with self.assertRaises(Exception) as cm:
            view(template_uid, output_format='')
        self.assertEquals(cm.exception.message,
                          "No 'output_format' found to generate this document")
        # if 'output_format' is not in available pod_formats of template, it raises an Exception
        self.assertNotIn('pdf', pod_template.get_available_formats())
        self.assertRaises(Exception, view)
        with self.assertRaises(Exception) as cm:
            view(template_uid, 'pdf')
        self.assertEquals(cm.exception.message,
                          "Asked output format 'pdf' is not available for template 'test_template'!")

        # right, ask available format
        self.assertIn('odt', pod_template.get_available_formats())
        generated_doc = view(template_uid, 'odt')

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
        template_uid = pod_template.UID()
        # Make sure can_be_generated will return False.
        pod_template.can_be_generated = lambda x: False
        self.assertTrue(not pod_template.can_be_generated(self.portal))

        view = self.portal.restrictedTraverse('@@document-generation')
        unauthorized_raised = False
        try:
            view(template_uid, 'odt')
        except Unauthorized:
            unauthorized_raised = True
        self.assertTrue(unauthorized_raised)

    def test_persistent_document_generation_call(self):
        """
        Check if documents are rendered correctly.
        """
        pod_template = self.test_podtemplate
        template_uid = pod_template.UID()
        generation_context = api.content.create(
            type='Folder',
            title='folder',
            id='test_folder',
            container=self.portal,
        )
        generation_view = generation_context.restrictedTraverse('@@persistent-document-generation')
        generation_view(template_uid, 'odt')

        msg = "File 'Document A' should have been created in folder."
        self.assertTrue(hasattr(generation_context, 'general-template'), msg)

        persistent_doc = getattr(generation_context, 'general-template')
        generated_doc = persistent_doc.getFile()
        # Check if (partial) data of the generated document is the same as the
        # pod_template odt file.
        original_doc = pod_template.get_file()
        generated = generated_doc.getBlob().open('r').read()
        self.assertTrue(original_doc.data[1200:2500] in generated)

        self.assertTrue(generated_doc.getFilename() == u'General template.odt')
        self.assertTrue(generated_doc.getContentType() == 'application/vnd.oasis.opendocument.text')

    def test_persistent_document_generation_on_non_folderish_context(self):
        """
        If the generation view is called on a non folderish the document file should be created
        on the parent.
        """
        from collective.documentgenerator.interfaces import isNotFolderishError

        pod_template = self.test_podtemplate
        template_uid = pod_template.UID()
        non_folderish = api.content.create(type='Document', id='doc', container=self.portal)
        generation_view = non_folderish.restrictedTraverse('@@persistent-document-generation')

        error_raised = False
        try:
            generation_view(template_uid, 'odt')
        except isNotFolderishError:
            error_raised = True

        msg = "A 'isNotFolderishError' exception should have been raised."
        self.assertTrue(error_raised, msg)


class TestCyclicMergesDetection(unittest.TestCase):
    """
    """

    layer = EXAMPLE_POD_TEMPLATE_INTEGRATION

    def setUp(self):
        super(TestCyclicMergesDetection, self).setUp()

        portal = api.portal.get()
        self.generation_view = portal.restrictedTraverse('@@document-generation')

        self.template_a = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_a',
            title='Modèle A',
            container=portal.podtemplates,
        )

        self.template_b = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_b',
            title='Modèle B',
            container=portal.podtemplates,
        )

        self.template_c = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_c',
            title='Modèle C',
            container=portal.podtemplates,
        )

        self.template_d = api.content.create(
            type='ConfigurablePODTemplate',
            id='template_d',
            title='Modèle D',
            container=portal.podtemplates,
        )

    def _test_detect_cycle(self, template, should_raise, msg=''):
        exception_raised = False
        try:
            self.generation_view._check_cyclic_merges(template)
        except CyclicMergeTemplatesException:
            exception_raised = True

        self.assertTrue(exception_raised == should_raise, msg)

    def test_detect_cycle_when_no_merge(self):
        template = self.template_a
        self.assertTrue(template.merge_templates == [])

        msg = "Cyclic merge detection should not raise anything when no subtemplates to merge."
        self._test_detect_cycle(template, should_raise=False, msg=msg)

    def test_detect_cycle_on_linear_merge(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a chain such as template_a -> template_b -> template_c
        template_a.set_merge_templates(template_b, 'pod_b')
        template_b.set_merge_templates(template_c, 'pod_c')

        msg = "Cyclic merge detection should not raise anything when import chain is not cyclic."
        self._test_detect_cycle(template_a, should_raise=False, msg=msg)

    def test_detect_cycle_on_linear_merge_with_duplicates(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a chain such as template_a -> template_b -> template_c
        #                                \_> template c
        template_a.set_merge_templates(template_b, 'pod_b')
        template_a.set_merge_templates(template_c, 'pod_c')
        template_b.set_merge_templates(template_c, 'pod_c')

        msg = "Cyclic merge detection should not raise anything when import chain is not cyclic."
        self._test_detect_cycle(template_a, should_raise=False, msg=msg)

    def test_detect_cycle_on_self_reference(self):
        template = self.template_a
        # import a configurable template on itself
        template.set_merge_templates(template, 'a')

        msg = "Cyclic merge detection should raise Exception when a template tries to import itself."
        self._test_detect_cycle(template, should_raise=True, msg=msg)

    def test_detect_cycle_on_simple_cycle(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a cyclic chain such as (template_a -> template_b -> template_c -> template_a)
        template_a.set_merge_templates(template_b, 'pod_b')
        template_b.set_merge_templates(template_c, 'pod_c')
        template_c.set_merge_templates(template_a, 'pod_a')

        msg = "Cyclic merge detection should raise Exception with cycle a -> b -> c -> a ."
        self._test_detect_cycle(template_a, should_raise=True, msg=msg)

    def test_detect_cycle_on_inner_cycle(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a an inner cyclic chain such as template_a -> (template_b -> template_c -> template_b)
        template_a.set_merge_templates(template_b, 'pod_b')
        template_b.set_merge_templates(template_c, 'pod_c')
        template_c.set_merge_templates(template_b, 'pod_b')

        msg = "Cyclic merge detection should raise Exception with cycle b -> c -> b ."
        self._test_detect_cycle(template_a, should_raise=True, msg=msg)
