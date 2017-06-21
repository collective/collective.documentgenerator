# -*- coding: utf-8 -*-

import os
from AccessControl import Unauthorized

from collective.documentgenerator.config import HAS_PLONE_5
from collective.documentgenerator.config import get_raiseOnError_for_non_managers
from collective.documentgenerator.content.pod_template import SubTemplate
from collective.documentgenerator.interfaces import CyclicMergeTemplatesException
from collective.documentgenerator.interfaces import PODTemplateNotFoundError
from collective.documentgenerator.testing import EXAMPLE_POD_TEMPLATE_INTEGRATION
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.testing import TEST_INSTALL_INTEGRATION
from collective.documentgenerator.utils import translate as _

from plone import api
from plone.app.testing import login
from plone.app.testing import TEST_USER_NAME
from plone.namedfile.file import NamedBlobFile

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
        self.assertEqual(
            cm.exception.message,
            "No 'output_format' found to generate this document"
        )
        # if 'output_format' is not in available pod_formats of template, it raises an Exception
        self.assertNotIn('pdf', pod_template.get_available_formats())
        self.assertRaises(Exception, view)
        with self.assertRaises(Exception) as cm:
            view(template_uid, 'pdf')
        self.assertEqual(
            cm.exception.message,
            "Asked output format 'pdf' is not available for template 'test_template'!"
        )

        # right, ask available format
        self.assertIn('odt', pod_template.get_available_formats())
        generated_doc = view(template_uid, 'odt')

        self.assertIn('application/vnd.oasis.opendocument.text', generated_doc)

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
        self.assertTrue('general-template-folder' in generation_context.objectIds(), msg)

        persistent_doc = getattr(generation_context, 'general-template-folder')
        if HAS_PLONE_5:
            generated_doc = persistent_doc.file
            filename = persistent_doc.file.filename
            content_type = persistent_doc.file.contentType
        else:
            generated_doc = persistent_doc.getFile()
            filename = generated_doc.getFilename()
            content_type = generated_doc.getContentType()
        self.assertIn('application/vnd.oasis.opendocument.text', generated_doc.data)

        self.assertEqual(filename, u'general-template-folder.odt')
        self.assertEqual(content_type, 'application/vnd.oasis.opendocument.text')

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

    def test__get_generation_context(self):
        pod_template = self.portal.podtemplates['test_template_bis']
        view = self.portal.podtemplates.restrictedTraverse('@@document-generation')
        hpv = view.get_generation_context_helper()
        # Check context variables
        self.assertDictEqual(view._get_generation_context(hpv, pod_template), {'details': '1',
                             'context': hpv.context, 'view': hpv})
        # Check configurable pod template
        self.assertDictEqual(view._get_generation_context(hpv, self.test_podtemplate),
                             {'context': hpv.context, 'view': hpv})

        rendered, filename, gen_context = view._generate_doc(pod_template, 'odt')

        # The gotten helper view (hpv) is not the used one at generation
        self.assertNotEquals(hpv, gen_context['view'])

        # Check generation context subtemplates without pre-rendering
        self.assertEqual(pod_template.merge_templates[0]['do_rendering'], False)
        self.assertIn('header', gen_context)
        self.assertIsInstance(gen_context['header'], SubTemplate)

        # Check generation context subtemplates with pre-rendering
        mt_conf = pod_template.merge_templates
        mt_conf[0]['do_rendering'] = True
        pod_template.merge_templates = mt_conf
        self.assertEqual(pod_template.merge_templates[0]['do_rendering'], True)
        # We call rendering to get new gen_context
        rendered, filename, gen_context = view._generate_doc(pod_template, 'odt')
        self.assertIsInstance(gen_context['header'], str)
        self.assertRegexpMatches(gen_context['header'], '.+(\.odt)$')

    def test_raiseOnError_for_non_managers(self):
        # create a POD template that will fail in every case
        current_path = os.path.dirname(__file__)
        failing_template_data = open(os.path.join(current_path, 'failing_template.odt'), 'r').read()
        failing_template = api.content.create(
            type='ConfigurablePODTemplate',
            id='failing_template',
            title=_(u'Failing template'),
            odt_file=NamedBlobFile(
                data=failing_template_data,
                contentType='application/vnd.oasis.opendocument.text',
                filename=u'modele_general.odt',
            ),
            pod_formats=['odt'],
            container=self.portal.podtemplates,
            exclude_from_nav=True
        )
        # create a user that is not Manager
        api.user.create(
            email='test@test.be',
            username='user',
            password='user',
            roles=['Member'],
            properties={})

        # disabled by default
        self.assertFalse(get_raiseOnError_for_non_managers())
        # when disabled, generating by anybody will always produce a document
        view = failing_template.restrictedTraverse('@@document-generation')
        template_UID = failing_template.UID()
        # generated for 'Manager'
        self.assertTrue('Manager' in api.user.get_current().getRoles())
        self.assertTrue(
            'mimetypeapplication/vnd.oasis.opendocument.text' in
            view(template_uid=template_UID, output_format='odt'))
        # generated for non 'Manager'
        login(self.portal, 'user')
        self.assertFalse('Manager' in api.user.get_current().getRoles())
        self.assertTrue(
            'mimetypeapplication/vnd.oasis.opendocument.text' in
            view(template_uid=template_UID, output_format='odt'))

        # enable raiseOnError_for_non_managers and test again
        login(self.portal, TEST_USER_NAME)
        api.portal.set_registry_record(
            'collective.documentgenerator.browser.controlpanel.'
            'IDocumentGeneratorControlPanelSchema.raiseOnError_for_non_managers',
            True)
        self.assertTrue(
            'mimetypeapplication/vnd.oasis.opendocument.text' in
            view(template_uid=template_UID, output_format='odt'))
        login(self.portal, 'user')
        # raises an error instead generating the document
        with self.assertRaises(Exception) as cm:
            view(template_uid=template_UID, output_format='odt')
        self.assertTrue(
            u'Error while evaluating expression "view.unknown_method()".' in
            cm.exception.message)


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

        msg = 'Cyclic merge detection should not raise anything when no subtemplates to merge.'
        self._test_detect_cycle(template, should_raise=False, msg=msg)

    def test_detect_cycle_on_linear_merge(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a chain such as template_a -> template_b -> template_c
        template_a.set_merge_templates(template_b, 'pod_b')
        template_b.set_merge_templates(template_c, 'pod_c')

        msg = 'Cyclic merge detection should not raise anything when import chain is not cyclic.'
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

        msg = 'Cyclic merge detection should not raise anything when import chain is not cyclic.'
        self._test_detect_cycle(template_a, should_raise=False, msg=msg)

    def test_detect_cycle_on_self_reference(self):
        template = self.template_a
        # import a configurable template on itself
        template.set_merge_templates(template, 'a')

        msg = 'Cyclic merge detection should raise Exception when a template tries to import itself.'
        self._test_detect_cycle(template, should_raise=True, msg=msg)

    def test_detect_cycle_on_simple_cycle(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a cyclic chain such as (template_a -> template_b -> template_c -> template_a)
        template_a.set_merge_templates(template_b, 'pod_b')
        template_b.set_merge_templates(template_c, 'pod_c')
        template_c.set_merge_templates(template_a, 'pod_a')

        msg = 'Cyclic merge detection should raise Exception with cycle a -> b -> c -> a .'
        self._test_detect_cycle(template_a, should_raise=True, msg=msg)

    def test_detect_cycle_on_inner_cycle(self):
        template_a = self.template_a
        template_b = self.template_b
        template_c = self.template_c
        # set a an inner cyclic chain such as template_a -> (template_b -> template_c -> template_b)
        template_a.set_merge_templates(template_b, 'pod_b')
        template_b.set_merge_templates(template_c, 'pod_c')
        template_c.set_merge_templates(template_b, 'pod_b')

        msg = 'Cyclic merge detection should raise Exception with cycle b -> c -> b .'
        self._test_detect_cycle(template_a, should_raise=True, msg=msg)
