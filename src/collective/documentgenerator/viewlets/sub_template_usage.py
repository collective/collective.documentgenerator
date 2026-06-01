# -*- coding: utf-8 -*-

from Acquisition import aq_parent
from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from collective.documentgenerator.content.pod_template import ISubTemplate
from collective.documentgenerator.utils import get_site_root_relative_path
from plone import api
from plone.app.layout.viewlets import ViewletBase
from plone.memoize.view import memoize
from Products.CMFPlone.utils import safe_unicode


class SubTemplateUsageViewlet(ViewletBase):
    """Display the POD templates that use the current sub-template in their
       'merge_templates' field, grouped by the folder path they live in."""

    def available(self):
        return ISubTemplate.providedBy(self.context) and bool(self.get_using_templates())

    @memoize
    def get_using_templates(self):
        """Return the list of templates referencing the current sub-template
           in their 'merge_templates' field."""
        catalog = api.portal.get_tool('portal_catalog')
        current_uid = self.context.UID()
        templates = []
        for brain in catalog(object_provides=IConfigurablePODTemplate.__identifier__):
            template = brain.getObject()
            for line in getattr(template, 'merge_templates', None) or []:
                if line.get('template') == current_uid:
                    templates.append(template)
                    break
        return templates

    def _title_path(self, obj):
        """Return a breadcrumb-like path made of the Title of each level
           between the site root (excluded) and ``obj`` (included)."""
        portal_path = '/'.join(api.portal.get().getPhysicalPath())
        titles = []
        current = obj.aq_inner
        while current is not None:
            current_path = '/'.join(current.getPhysicalPath())
            if current_path == portal_path or not current_path.startswith(portal_path):
                break
            titles.append(safe_unicode(current.Title()))
            current = aq_parent(current.aq_inner)
        return u' / '.join(reversed(titles))

    def get_using_templates_by_path(self):
        """Return a list of {'path', 'title_path', 'templates'} groups of the
           templates referencing the current sub-template, grouped by their
           container and sorted by path then by title."""
        grouped = {}
        for template in self.get_using_templates():
            parent = template.aq_inner.aq_parent
            path = get_site_root_relative_path(parent)
            grouped.setdefault(path, {'title_path': self._title_path(parent), 'templates': []})
            grouped[path]['templates'].append(template)
        result = []
        for path in sorted(grouped):
            group = grouped[path]
            group['templates'].sort(key=lambda t: t.Title().lower())
            result.append({'path': path, 'title_path': group['title_path'],
                           'templates': group['templates']})
        return result
