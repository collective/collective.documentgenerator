# -*- coding: utf-8 -*-

from collective.documentgenerator.browser.table import SubTemplateColumn
from collective.documentgenerator.browser.table import SubTemplateUsagePathColumn
from collective.documentgenerator.browser.table import SubTemplateUsageTemplatesColumn
from collective.documentgenerator.testing import PODTemplateIntegrationTest
from plone import api
from Products.CMFPlone.utils import _createObjectByType


class TestSubTemplatesUsageView(PODTemplateIntegrationTest):
    """Test the 'sub-templates-usage' view.

    The demo profile creates a single 'sub_template' (title 'Header') in
    'podtemplates', used by 'test_template_multiple' and 'test_template_bis'.
    """

    def setUp(self):
        super(TestSubTemplatesUsageView, self).setUp()
        self.view = self.portal.restrictedTraverse("@@sub-templates-usage")

    def _rows(self):
        """Add a second usage group for the demo sub-template and an unused sub-template.

        Returns the 3 table rows the view then builds:

        +------------------------+----------------------+--------------------------+
        | Sub-template           | Path                 | Using templates          |
        +========================+======================+==========================+
        | Header                 | POD Templates        | Collection template      | rows[0]
        | header, zeta_var       |                      | Multiple format template |
        +------------------------+----------------------+--------------------------+
        |                        | POD Templates / Zeta | In Zeta template         | rows[1]
        +------------------------+----------------------+--------------------------+
        | Zeta / In Zeta         | -                    | not used                 | rows[2]
        +------------------------+----------------------+--------------------------+

        rows[1] is a continuation row: same sub-template, second path group, so its
        first cell stays empty ('first' is False). rows[2] has 'group' set to None.
        The two merge variables of 'Header' differ, which turns its cell red.
        """
        pod = self.portal.podtemplates
        folder = _createObjectByType("Folder", pod, "folder_z", title=u"Zeta")
        api.content.create(type="SubTemplate", id="st_z", title=u"In Zeta", container=folder)
        api.content.create(type="ConfigurablePODTemplate", id="in_zeta", title=u"In Zeta template",
                           container=folder,
                           merge_templates=[{"template": pod.sub_template.UID(),
                                             "pod_context_name": u"zeta_var", "do_rendering": False}])
        self.view.update()
        return self.view.table.results

    def test_sub_templates_usage(self):
        entries = self.view.sub_templates_usage()
        # one entry per sub-template (here the single demo 'sub_template')
        self.assertEqual([e["sub_template"].getId for e in entries], ["sub_template"])
        self.assertEqual(entries[0]["sub_template_uid"], self.portal.podtemplates.sub_template.UID())
        # the only sub-template defines the whole common path -> empty rel_path
        self.assertEqual(entries[0]["rel_path"], u"")
        # both using templates share the same folder -> one group, sorted by title
        groups = entries[0]["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual([t.getId() for t in groups[0]["templates"]], ["test_template_bis", "test_template_multiple"])

    def test_rel_path_strips_common_part(self):
        # add two more sub-templates in distinct sub-folders of 'podtemplates'
        pod = self.portal.podtemplates
        # following escape disallowed !
        folder_z = _createObjectByType("Folder", pod, "folder_z", title=u"Zeta")
        folder_a = _createObjectByType("Folder", pod, "folder_a", title=u"Alpha")
        api.content.create(type="SubTemplate", id="st_z", title=u"In Zeta", container=folder_z)
        api.content.create(type="SubTemplate", id="st_a", title=u"In Alpha", container=folder_a)

        entries = self.view.sub_templates_usage()
        rel_paths = [e["rel_path"] for e in entries]
        # 'podtemplates' is common to every sub-template and is stripped away;
        # the demo sub-template sits directly in 'podtemplates' -> empty rel_path.
        self.assertEqual(rel_paths, [u"", u"Alpha", u"Zeta"])
        # entries are ordered by the first-column path (rel_path) then by title
        self.assertEqual(
            [e["sub_template"].getId for e in entries],
            ["sub_template", "st_a", "st_z"],
        )
        # the common 'podtemplates' segment never appears in the displayed path
        pod_title = pod.Title()
        self.assertFalse(any(pod_title in rel_path for rel_path in rel_paths))

    def test_update(self):
        rows = self._rows()
        self.assertEqual([col.__name__ for col in self.view.table.columns],
                         ["SubTemplateColumn", "SubTemplateUsagePathColumn", "SubTemplateUsageTemplatesColumn"])
        # one row per (sub-template, path group), 'first' marking a group start
        self.assertEqual([(r["sub_template"].getId, r["first"], r["group"] is None) for r in rows],
                         [("sub_template", True, False),
                          ("sub_template", False, False),
                          ("st_z", True, True)])
        # the whole page renders the table
        self.assertIn(u'class="listing nosort sub-templates-usage"', self.view())

    def test_SubTemplateColumn(self):
        rows = self._rows()
        column = SubTemplateColumn(self.view.context, self.view.request, self.view.table)
        # the merge variables of every using template, whatever their path group
        self.assertEqual(column.renderCell(rows[0]),
                         u'<a href="http://nohost/plone/podtemplates/sub_template">Header</a>'
                         u'<div class="pod-context-name">header, zeta_var</div>')
        # a continuation row leaves the cell empty, as the removed rowspan did
        self.assertEqual(column.renderCell(rows[1]), u"")
        # an unused sub-template has no path and no variable to show
        self.assertEqual(column.renderCell(rows[2]),
                         u'<span>Zeta</span> / '
                         u'<a href="http://nohost/plone/podtemplates/folder_z/st_z">In Zeta</a>')
        # a single variable name, shared by every using template, is displayed once
        self.portal.podtemplates.folder_z.in_zeta.merge_templates[0]["pod_context_name"] = u"header"
        self.assertIn(u'<div class="pod-context-name">header</div>', column.renderCell(rows[0]))

    def test_get_pod_context_names(self):
        rows = self._rows()
        pod = self.portal.podtemplates
        column = SubTemplateColumn(self.view.context, self.view.request, self.view.table)
        self.assertEqual(column.get_pod_context_names(rows[0]), [u"header", u"zeta_var"])
        # nothing to collect for a sub-template used by no template
        self.assertEqual(column.get_pod_context_names(rows[2]), [])
        # templates not merging the sub-template, without the field at all or with an
        # empty variable name are all skipped
        item = {"sub_template_uid": pod.sub_template.UID(),
                "groups": [{"templates": [pod.test_template, pod.test_style_template]}]}
        self.assertEqual(column.get_pod_context_names(item), [])
        pod.test_template_multiple.merge_templates[0]["pod_context_name"] = u""
        item["groups"] = [{"templates": [pod.test_template_multiple]}]
        self.assertEqual(column.get_pod_context_names(item), [])

    def test_conflicting_variables_cell(self):
        self._rows()
        self.assertIn(u'class="sub-template-column conflicting-variables"', self.view())
        # the same variable name everywhere: the cell keeps its plain class
        self.portal.podtemplates.folder_z.in_zeta.merge_templates[0]["pod_context_name"] = u"header"
        self.assertNotIn(u"conflicting-variables", self.view())

    def test_SubTemplateUsagePathColumn(self):
        rows = self._rows()
        column = SubTemplateUsagePathColumn(self.view.context, self.view.request, self.view.table)
        self.assertEqual(column.header, u"sub_template_usage_path")
        self.assertEqual(column.renderCell(rows[0]), u"POD Templates")
        self.assertEqual(column.renderCell(rows[1]), u"POD Templates / Zeta")
        # an unused sub-template has no path to show
        self.assertEqual(column.renderCell(rows[2]), u"-")

    def test_SubTemplateUsageTemplatesColumn(self):
        rows = self._rows()
        column = SubTemplateUsageTemplatesColumn(self.view.context, self.view.request, self.view.table)
        self.assertEqual(column.header, u"sub_template_usage_templates")
        self.assertEqual(column.renderCell(rows[0]),
                         u'<ul><li><a href="http://nohost/plone/podtemplates/test_template_bis">'
                         u'Collection template</a></li>'
                         u'<li><a href="http://nohost/plone/podtemplates/test_template_multiple">'
                         u'Multiple format template</a></li></ul>')
        self.assertEqual(column.renderCell(rows[1]),
                         u'<ul><li><a href="http://nohost/plone/podtemplates/folder_z/in_zeta">'
                         u'In Zeta template</a></li></ul>')
        # the not-used row shows an emphasized label instead of links
        self.assertRegexpMatches(column.renderCell(rows[2]), u"^<em>[^<]+</em>$")
