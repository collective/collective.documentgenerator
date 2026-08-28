# -*- coding: utf-8 -*-

from collective.documentgenerator.browser.table import SubTemplateUsageTable
from collective.documentgenerator.content.pod_template import ISubTemplate
from collective.documentgenerator.utils import get_pod_templates_using
from collective.documentgenerator.utils import group_templates_by_path
from plone.app.layout.viewlets import ViewletBase
from plone.memoize.view import memoize


class SubTemplateUsageViewlet(ViewletBase):
    """Display the POD templates that use the current sub-template in their
       'merge_templates' field, grouped by the folder path they live in."""

    __table__ = SubTemplateUsageTable

    def update(self):
        super(SubTemplateUsageViewlet, self).update()
        self.table = self.__table__(self.context, self.request)
        self.table.__name__ = u"sub-template-usage"
        self.table.results = _sub_template_usage_groups_to_rows(
            [{"sub_template": None, "rel_path": u"", "sub_template_uid": self.context.UID(),
              "groups": self.get_using_templates_by_path()}])
        self.table.update()

    def available(self):
        return ISubTemplate.providedBy(self.context) and bool(self.get_using_templates())

    @memoize
    def get_using_templates(self):
        """Return the list of templates referencing the current sub-template
           in their 'merge_templates' field."""
        return get_pod_templates_using(self.context)

    def get_using_templates_by_path(self):
        """Return a list of {'path', 'title_path', 'templates'} groups of the
           templates referencing the current sub-template, grouped by their
           container and sorted by path then by title."""
        return group_templates_by_path(self.get_using_templates())


def _sub_template_usage_groups_to_rows(entries):
    """Return the usage table rows for `entries`, one per (sub-template, path group).

    A row carries the entry keys plus 'group' (None when the sub-template is used by no
    template) and 'first' (False on a group continuation row, where the sub-template cell
    stays empty since z3c.table has no rowspan). 'groups' is kept on every row so that a
    cell can look at the whole sub-template, not only at its own group.
    """
    rows = []
    for entry in entries:
        for i, group in enumerate(entry['groups'] or [None]):
            rows.append({'sub_template': entry['sub_template'], 'rel_path': entry['rel_path'],
                         'sub_template_uid': entry['sub_template_uid'], 'group': group,
                         'groups': entry['groups'], 'first': i == 0})
    return rows
