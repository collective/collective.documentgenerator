# -*- coding: utf-8 -*-

import appy
from StringIO import StringIO
from plone import api
from collective.documentgenerator.demo.helper import DemoHelperView
from collective.documentgenerator.testing import ArchetypesIntegrationTests


class TestBaseHelperViewMethods(ArchetypesIntegrationTests):
    """
    Test base helper view's methods.
    """

    def setUp(self):
        super(TestBaseHelperViewMethods, self).setUp()
        self.view = self.AT_topic.unrestrictedTraverse('@@document_generation_helper_view')

    def test_translate_method(self):
        msgid = u'month_may'
        translation = self.view.translate(msgid, domain='plonelocales')
        self.assertTrue(translation == u'May')

    def test_getDGHV(self):
        new_dghv = self.view.getDGHV(self.portal['podtemplates'])
        isinstance(new_dghv, DemoHelperView)
        self.assertEqual(new_dghv.real_context, self.portal['podtemplates'])
        self.assertEqual(new_dghv.display('title'), 'POD Templates')

    def test_get_state(self):
        # no workflow
        self.assertEqual(self.view.get_state(title=True), '-')

    def test_context_var(self):
        pod_template = self.portal.podtemplates.get('test_template_multiple')
        # Empty context_variables attribute
        self.assertIsNone(pod_template.context_variables)

        doc = api.content.create(type='Document', id='doc', container=self.portal)
        view = doc.restrictedTraverse('@@document-generation')
        document_template = pod_template.get_file()
        helper_view = view.get_generation_context_helper()

        generation_context = view._get_generation_context(helper_view, pod_template=pod_template)
        renderer = appy.pod.renderer.Renderer(StringIO(document_template.data), generation_context, 'dummy.odt')
        helper_view._set_appy_renderer(renderer)

        # unknown variable
        self.assertEqual(helper_view.context_var('dexter', 'undefined'), 'undefined')

        # add a context variable on pod template
        pod_template.context_variables = [{'name': u'dexter', 'value': u'1'}]
        generation_context = view._get_generation_context(helper_view, pod_template=pod_template)
        renderer = appy.pod.renderer.Renderer(StringIO(document_template.data), generation_context, 'dummy.odt')
        helper_view._set_appy_renderer(renderer)
        self.assertEqual(helper_view.context_var('dexter', 'undefined'), u'1')
