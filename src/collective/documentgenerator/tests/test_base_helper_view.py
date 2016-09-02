# -*- coding: utf-8 -*-

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
