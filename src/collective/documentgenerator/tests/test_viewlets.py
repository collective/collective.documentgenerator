# -*- coding: utf-8 -*-

from collective.documentgenerator.testing import PODTemplateIntegrationTest
from collective.documentgenerator.viewlets.sub_template_usage import _sub_template_usage_groups_to_rows
from collective.documentgenerator.viewlets.sub_template_usage import SubTemplateUsageViewlet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class UsageViewlet(SubTemplateUsageViewlet):
    """The zcml registration binds the template, so bind it by hand to render the viewlet."""

    index = ViewPageTemplateFile("../viewlets/sub_template_usage.pt")


class TestSubTemplateUsageViewlet(PODTemplateIntegrationTest):
    """Test the 'sub-template-usage' viewlet on a SubTemplate.

    The demo profile creates a 'sub_template' used by 'test_template_multiple'
    and 'test_template_bis', both in the 'podtemplates' folder.
    """

    def setUp(self):
        super(TestSubTemplateUsageViewlet, self).setUp()
        portal = self.portal
        sub_template = portal.podtemplates.sub_template
        self.viewlet = UsageViewlet(sub_template, portal.REQUEST, None, None)

    def test_available_and_using_templates_grouped_by_path(self):
        self.assertTrue(self.viewlet.available())
        groups = self.viewlet.get_using_templates_by_path()
        # both templates live in the same folder -> a single group, sorted by title
        self.assertEqual(len(groups), 1)
        self.assertEqual([t.getId() for t in groups[0]['templates']],
                         ['test_template_bis', 'test_template_multiple'])

    def test_update(self):
        self.viewlet.update()
        # the sub-template is the context here, so its column and its merge variable are dropped
        self.assertEqual([col.__name__ for col in self.viewlet.table.columns],
                         ['SubTemplateUsagePathColumn', 'SubTemplateUsageTemplatesColumn'])
        self.assertEqual(len(self.viewlet.table.results), 1)

    def test_render(self):
        self.viewlet.update()
        rendered = self.viewlet.render()
        self.assertEqual(rendered.count(u'<th>'), 2)
        self.assertIn(u'<li><a href="http://nohost/plone/podtemplates/test_template_bis">'
                      u'Collection template</a></li>', rendered)
        # the sub-template column is hidden, and with it the merge variable it carries
        self.assertNotIn(u'sub-template-column', rendered)
        self.assertNotIn(u'pod-context-name', rendered)

    def test_sub_template_usage_groups_to_rows(self):
        entries = [{'sub_template': 'brain1', 'rel_path': u'A', 'sub_template_uid': 'uid1',
                    'groups': [{'title_path': u'p1'}, {'title_path': u'p2'}]},
                   {'sub_template': 'brain2', 'rel_path': u'', 'sub_template_uid': 'uid2',
                    'groups': []}]
        rows = _sub_template_usage_groups_to_rows(entries)

        # one row per group, 'first' only on the first one; a sub-template used by no
        # template still gets a row, marked by a None group
        self.assertEqual([(r['sub_template_uid'], r['first'], r['group']) for r in rows],
                         [('uid1', True, {'title_path': u'p1'}),
                          ('uid1', False, {'title_path': u'p2'}),
                          ('uid2', True, None)])

        # the sub-template column data is carried on every row of the group
        self.assertEqual([(r['sub_template'], r['rel_path']) for r in rows[:2]],
                         [('brain1', u'A'), ('brain1', u'A')])
