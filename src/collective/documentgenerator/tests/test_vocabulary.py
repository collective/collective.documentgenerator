# -*- coding: utf-8 -*-

from collective.documentgenerator.config import POD_FORMATS
from collective.documentgenerator.testing import BaseTest
from collective.documentgenerator.testing import POD_TEMPLATE_INTEGRATION
from plone import api
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory


class TestVocabularies(BaseTest):
    layer = POD_TEMPLATE_INTEGRATION

    def test_portal_type_vocabulary_factory_registration(self):
        """
        Portal type voc factory should be registered as a named utility.
        """
        factory_name = 'collective.documentgenerator.PortalTypes'
        self.assertTrue(queryUtility(IVocabularyFactory, factory_name))

    def test_portal_type_vocabulary_values(self):
        """
        Test some Portal_type values.
        """
        voc_name = 'collective.documentgenerator.PortalTypes'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        permissions_voc = vocabulary(self.portal)
        self.assertTrue('Plone Site' in permissions_voc)
        self.assertTrue('Event' in permissions_voc)

    def test_style_vocabulary_factory_registration(self):
        """
        Styles voc factory should be registered as a named utility.
        """
        factory_name = 'collective.documentgenerator.StyleTemplates'
        self.assertTrue(queryUtility(IVocabularyFactory, factory_name))

    def test_style_vocabulary_values(self):
        """
        Test some style values.
        """
        voc_name = 'collective.documentgenerator.StyleTemplates'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        style_voc = vocabulary(self.portal)
        style_template = self.portal.podtemplates.test_style_template
        self.assertTrue(style_template.UID() in style_voc)

    def test_merge_templates_vocabulary_factory_registration(self):
        """
        Merge templates voc factory should be registered as a named utility.
        """
        factory_name = 'collective.documentgenerator.MergeTemplates'
        self.assertTrue(queryUtility(IVocabularyFactory, factory_name))

    def test_merge_templates_vocabulary_values(self):
        """
        Test some merge template values.
        """
        voc_name = 'collective.documentgenerator.MergeTemplates'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        merge_templates_voc = vocabulary(self.portal)
        pod_template = self.portal.podtemplates.test_template
        self.assertTrue(pod_template.UID() in merge_templates_voc)

    def test_pod_formats_vocabulary(self):
        """
        Test the pod_formats vocabulary.
        """
        voc_name = 'collective.documentgenerator.Formats'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        voc = vocabulary(self.portal)
        for pod_format, label in POD_FORMATS:
            self.assertTrue(pod_format in voc)

    def test_mailing_loop_enabled_vocabulary(self):
        """
        Test the EnabledMailingLoopTemplates vocabulary.
        """
        voc_name = 'collective.documentgenerator.EnabledMailingLoopTemplates'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        voc = vocabulary(self.portal)
        loop_template = self.portal.podtemplates.get('loop_template')
        self.assertListEqual([loop_template.UID()], [t.value for t in voc])
        loop_template.enabled = False
        voc = vocabulary(self.portal)
        self.assertListEqual([], [t for t in voc])

    def test_mailing_loop_all_vocabulary(self):
        """
        Test the AllMailingLoopTemplates vocabulary.
        """
        voc_name = 'collective.documentgenerator.AllMailingLoopTemplates'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        voc = vocabulary(self.portal.podtemplates)
        loop_template = self.portal.podtemplates.get('loop_template')
        self.assertListEqual([loop_template.UID()], [t.value for t in voc])
        loop_template.enabled = False
        voc = vocabulary(self.portal)
        self.assertListEqual([loop_template.UID()], [t.value for t in voc])

    def test_PTMCTV(self):
        pod_template = self.portal.podtemplates.get('test_template_possibly_mailed')
        view = pod_template.restrictedTraverse('@@view')
        view.update()
        # the title from the vocabulary is well rendered
        self.assertIn('Mailing loop template', view.widgets['mailing_loop_template'].render())
        # We deactivate the loop template, the missing value is managed
        loop_template = self.portal.podtemplates.get('loop_template')
        loop_template_uid = loop_template.UID()
        loop_template.enabled = False
        voc_inst = queryUtility(IVocabularyFactory, 'collective.documentgenerator.EnabledMailingLoopTemplates')
        self.assertListEqual([], [t.value for t in voc_inst(pod_template)])
        view.updateWidgets()
        self.assertIn('Mailing loop template', view.widgets['mailing_loop_template'].render())
        # We remove the loop template, the missing value cannot be managed anymore
        api.content.delete(obj=loop_template)
        view.updateWidgets()
        self.assertNotIn('Mailing loop template', view.widgets['mailing_loop_template'].render())
        self.assertIn('Valeur manquante', view.widgets['mailing_loop_template'].render())
        self.assertIn(loop_template_uid, view.widgets['mailing_loop_template'].render())

    def test_existing_pod_template_vocabulary(self):
        """
        Test the ExistingPODTemplate vocabulary.
        """
        voc_name = 'collective.documentgenerator.ExistingPODTemplate'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        voc = vocabulary(self.portal)
        test_podtemplate = self.portal.podtemplates.get('test_template_reusable')
        self.assertListEqual([test_podtemplate.UID()], [t.value for t in voc])

        reusable_template_2 = self.portal.podtemplates.get('test_template_possibly_mailed')
        reusable_template_2.is_reusable = True

        voc = vocabulary(self.portal)
        self.assertListEqual([reusable_template_2.UID(), test_podtemplate.UID()], [t.value for t in voc])

    def test_all_pod_templates_vocabulary(self):
        """
        Test the AllPODTemplate vocabulary.
        """
        voc_name = 'collective.documentgenerator.AllPODTemplateWithFile'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        voc = vocabulary(self.portal)
        self.assertEquals(len(voc), 9)

    def test_all_value_in_all_pod_templates_vocabulary(self):
        """
        Test the 'all' value is in the AllPODTemplate vocabulary.
        """
        voc_name = 'collective.documentgenerator.AllPODTemplateWithFile'
        vocabulary = queryUtility(IVocabularyFactory, voc_name)
        voc = vocabulary(self.portal)
        self.assertIn('all', voc)
