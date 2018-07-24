# -*- coding: utf-8 -*-

from collective.documentgenerator.browser.table import PathColumn
from collective.documentgenerator.browser.table import TitleColumn
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from plone import api
from Products.CMFPlone.utils import _createObjectByType


class TestTemplatesListingView(PODTemplateIntegrationTest):

    """Test Dexterity helper view."""

    def setUp(self):
        super(TestTemplatesListingView, self).setUp()
        # by pass allowed types restriction
        sub_folder = _createObjectByType("Folder", self.portal.podtemplates, 'sub_folder', title='Subfolder')
        self.sft = api.content.create(type='ConfigurablePODTemplate', id='sub_folder_template', container=sub_folder,
                                      title='Sub folder template')
        self.ot = api.content.create(type='ConfigurablePODTemplate', id='other_template', container=self.portal,
                                     title='Other template')
        self.view = self.portal.podtemplates.restrictedTraverse('dg-templates-listing')
        self.view.update()

    def test_view_update(self):
        self.assertIsNone(self.view.depth)
        self.assertTrue(self.view.local_search)
        self.view()
        # we found 11 example templates + 1 sub_template
        self.assertEqual(len(self.view.table.results), 12)

        self.view(local_search=True, search_depth=1)
        # we found 11 example templates
        self.assertEqual(len(self.view.table.results), 11)

        self.view(local_search=False, search_depth=1)
        # we found all existing templates
        self.assertEqual(len(self.view.table.results), 13)

        self.view.request.set('local_search', '1')
        self.view.request.set('search_depth', '1')
        self.view()
        # we found 11 example templates
        self.assertEqual(len(self.view.table.results), 11)

        # check order
        self.view(local_search=False)
        # we found all existing templates
        self.assertListEqual(
            [o.id for o in self.view.table.results],
            ['other_template',
             'test_style_template',
             'test_style_template_2',
             'sub_template',
             'loop_template',
             'test_template',
             'test_template_multiple',
             'test_template_bis',
             'test_ods_template',
             'test_template_possibly_mailed',
             'test_template_reusable',
             'test_template_reuse',
             'sub_folder_template'])

    def test_TitleColumn(self):
        column = TitleColumn(self.view.context, self.view.request, self.view.table)
        item = self.test_podtemplate
        self.assertEquals(column.renderHeadCell(), u'Titre')
        self.assertEquals(column.renderCell(item),
                          u'<a href="http://nohost/plone/podtemplates/test_template" class="pretty_link state-private">'
                          u'<span class="pretty_link_icons"><img title="Modèle de document POD restreint" '
                          u'src="http://nohost/plone/++resource++collective.documentgenerator/podtemplate.png" />'
                          u'</span><span class="pretty_link_content">General template</span></a>')

    def test_PathColumn(self):
        column = PathColumn(self.view.context, self.view.request, self.view.table)
        self.assertEquals(column.renderHeadCell(), u'Chemin relatif')
        # test rel_path_title
        column.rel_path_title('../other_template')
        self.assertEqual(self.view.table.paths['../other_template'], u'../Other template')
        column.rel_path_title('..')
        self.assertEqual(self.view.table.paths['..'], u'..')
        column.rel_path_title('sub_folder/sub_folder_template')
        self.assertEqual(self.view.table.paths['sub_folder/sub_folder_template'], u'Subfolder/Sub folder template')
        # test rendering
        item = self.test_podtemplate
        self.assertEquals(column.renderCell(item), u'<a href="http://nohost/plone/podtemplates" target="_blank">-</a>')
        self.assertEquals(column.renderCell(self.ot), u'<a href="http://nohost/plone" target="_blank">..</a>')
        self.assertEquals(column.renderCell(self.sft), u'<a href="http://nohost/plone/podtemplates/sub_folder" '
                                                       u'target="_blank">Subfolder</a>')
