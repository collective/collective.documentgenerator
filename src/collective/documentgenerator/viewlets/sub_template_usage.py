# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import ISubTemplate
from collective.documentgenerator.utils import get_pod_templates_using
from collective.documentgenerator.utils import group_templates_by_path
from plone.app.layout.viewlets import ViewletBase
from plone.memoize.view import memoize


class SubTemplateUsageViewlet(ViewletBase):
    """Display the POD templates that use the current sub-template in their
       'merge_templates' field, grouped by the folder path they live in."""

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
