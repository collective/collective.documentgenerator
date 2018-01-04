# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import _createObjectByType
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from plone import api


class TestTemplatesListingView(PODTemplateIntegrationTest):

    """Test Dexterity helper view."""

    def setUp(self):
        super(TestTemplatesListingView, self).setUp()
        # by pass allowed types restriction
        sub_folder = _createObjectByType("Folder", self.portal.podtemplates, 'sub_folder')
        api.content.create(type='ConfigurablePODTemplate', id='sub_folder_template', container=sub_folder)
        api.content.create(type='ConfigurablePODTemplate', id='other_template', container=self.portal)
        self.view = self.portal.podtemplates.restrictedTraverse('dg-templates-listing')

    def test_view_update(self):
        self.assertIsNone(self.view.depth)
        self.assertTrue(self.view.local_search)
        self.view()
        # we found 9 example templates + 1 sub_template
        self.assertEqual(len(self.view.table.results), 10)

        self.view(local_search=True, search_depth=1)
        # we found 9 example templates
        self.assertEqual(len(self.view.table.results), 9)

        self.view(local_search=False, search_depth=1)
        # we found all existing templates
        self.assertEqual(len(self.view.table.results), 11)

        self.view.request.set('local_search', '1')
        self.view.request.set('search_depth', '1')
        self.view()
        # we found 9 example templates
        self.assertEqual(len(self.view.table.results), 9)

        # check order
        self.view(local_search=False)
        # we found all existing templates
        self.assertListEqual([o.id for o in self.view.table.results],
                             ['other_template', 'test_style_template', 'test_style_template_2', 'sub_template',
                              'loop_template', 'test_template', 'test_template_multiple', 'test_template_bis',
                              'test_ods_template', 'test_template_possibly_mailed', 'sub_folder_template'])
