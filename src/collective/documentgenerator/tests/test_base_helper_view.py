# -*- coding: utf-8 -*-

from collective.documentgenerator.config import HAS_PLONE_5
from collective.documentgenerator.demo.helper import ATDemoHelperView
from collective.documentgenerator.demo.helper import BaseDemoHelperView
from collective.documentgenerator.demo.helper import DXDemoHelperView
from collective.documentgenerator.testing import DexterityIntegrationTests
from plone import api
from StringIO import StringIO

import appy


class TestBaseHelperViewMethods(DexterityIntegrationTests):
    """
    Test base helper view's methods.
    """

    def setUp(self):
        super(TestBaseHelperViewMethods, self).setUp()
        self.view = self.content.unrestrictedTraverse(
            '@@document_generation_helper_view')

    def test_translate_method(self):
        msgid = u'month_may'
        translation = self.view.translate(msgid, domain='plonelocales')
        self.assertTrue(translation == u'Mai')

    def test_getDGHV(self):
        new_dghv = self.view.getDGHV(self.portal['podtemplates'])
        self.assertTrue(isinstance(new_dghv, BaseDemoHelperView))
        if HAS_PLONE_5:
            self.assertTrue(isinstance(new_dghv, DXDemoHelperView))
        else:
            self.assertTrue(isinstance(new_dghv, ATDemoHelperView))
        self.assertEqual(new_dghv.real_context, self.portal['podtemplates'])
        self.assertEqual(new_dghv.display('title'), 'POD Templates')

    def test_get_state(self):
        # use 'simple_publication_workflow'
        self.assertEqual(self.view.get_state(title=True), 'Private')

    def test_context_var(self):
        pod_template = self.portal.podtemplates.get('test_template_multiple')
        # Empty context_variables attribute
        self.assertIsNone(pod_template.context_variables)

        doc = api.content.create(type='Document', id='mydoc', container=self.portal)
        view = doc.restrictedTraverse('@@document-generation')
        view(template_uid=pod_template.UID(), output_format='odt')
        document_template = pod_template.get_file()
        helper_view = view.get_generation_context_helper()

        generation_context = view._get_generation_context(helper_view, pod_template=pod_template)
        renderer = appy.pod.renderer.Renderer(StringIO(document_template.data), generation_context, 'dummy.odt')
        helper_view._set_appy_renderer(renderer)

        # unknown variable
        self.assertEqual(helper_view.context_var('dexter', 'undefined'), 'undefined')

        # None value (after edition, an empty value is replaced by None)
        pod_template.context_variables = [{'name': u'dexter', 'value': None}]
        generation_context = view._get_generation_context(helper_view, pod_template=pod_template)
        renderer = appy.pod.renderer.Renderer(StringIO(document_template.data), generation_context, 'dummy.odt')
        helper_view._set_appy_renderer(renderer)
        self.assertEqual(helper_view.context_var('dexter'), '')  # default is '' by default

        # add a context variable on pod template
        pod_template.context_variables = [{'name': u'dexter', 'value': u'1'}]
        generation_context = view._get_generation_context(helper_view, pod_template=pod_template)
        renderer = appy.pod.renderer.Renderer(StringIO(document_template.data), generation_context, 'dummy.odt')
        helper_view._set_appy_renderer(renderer)
        self.assertEqual(helper_view.context_var('dexter', 'undefined'), u'1')

    def test_display_phone(self):
        # belgian phone numbers
        self.assertEqual(self.view.display_phone(phone=u'081000000'), u'081 00 00 00')
        self.assertEqual(self.view.display_phone(phone=u'+3281000000'), u'081 00 00 00')
        self.assertEqual(self.view.display_phone(phone=u'081000000', country='BE'), u'081 00 00 00')
        self.assertEqual(self.view.display_phone(phone=u'081000000', format='nat'), u'081 00 00 00')
        self.assertEqual(self.view.display_phone(phone=u'081000000', format='int'), u'+32 81 00 00 00')
        # bad phone numbers
#        self.assertEqual(self.view.display_phone(phone=u'abcdefgh'), u"Bad phone number: 'abcdefgh'")
        self.assertEqual(self.view.display_phone(phone=u'abcdefgh'),
                         u"Numéro de téléphone non reconnu: 'abcdefgh'")

#        self.assertEqual(self.view.display_phone(phone='0810000000'), u"Invalid phone number: '0810000000'")
        self.assertEqual(self.view.display_phone(phone='0810000000'), u"Numéro de téléphone non valide: '0810000000'")
#        self.assertEqual(self.view.display_phone(phone='081000000', country='FR'),
#                         u"Invalid phone number: '081000000'")
        self.assertEqual(self.view.display_phone(phone='081000000', country='FR'),
                         u"Numéro de téléphone non valide: '081000000'")
        # international phone numbers
        self.assertEqual(self.view.display_phone(phone=u'0033100000000'), u'+33 1 00 00 00 00')
        self.assertEqual(self.view.display_phone(phone=u'+33100000000'), u'+33 1 00 00 00 00')
        self.assertEqual(self.view.display_phone(phone=u'+33100000000', country='FR'), u'01 00 00 00 00')
        # formating phone numbers
        self.assertEqual(self.view.display_phone(phone='081000000', pattern='/.'), u'081/00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern='/.,'), u'081/00.00,00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern='/ '), u'081/00 00 00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern='.'), u'081.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern='.|'), u'081.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern=''), u'081 00 00 00')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern='|-.'), u'+32-81.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern='.|-.'), u'+32-81.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern='.'), u'+32 81 00 00 00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern=[['/', '.']]), u'081/00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern=[['/', ' ']]), u'081/00 00 00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern=[['.']]), u'081.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern=[['.'], ['']]), u'081.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', pattern=[['']]), u'081000000')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern=[[], ['-', '.']]),
                         u'+32-81.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern=[['.'], ['-', '.']]),
                         u'+32-81.00.00.00')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern=[['.']]),
                         u'+32 81 00 00 00')
        self.assertEqual(self.view.display_phone(phone='081000000', format='int', pattern=[[], [' (0)', ' ']]),
                         u'+32 (0)81 00 00 00')

    def test_iterable_as_columns(self):
        self.assertListEqual(self.view.iterable_in_columns(None), [])
        self.assertListEqual(self.view.iterable_in_columns([]), [])
        self.assertListEqual(self.view.iterable_in_columns([1, 2, 3]), [[1], [2], [3]])
        self.assertListEqual(self.view.iterable_in_columns([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])
        self.assertListEqual(self.view.iterable_in_columns([1, 2, 3, 4, 5], 3), [[1, 2, 3], [4, 5]])
        self.assertListEqual(self.view.iterable_in_columns([1, 2, 3, 4, 5], 5), [[1, 2, 3, 4, 5]])
        self.assertListEqual(self.view.iterable_in_columns('12345', 5), [['1', '2', '3', '4', '5']])
