# -*- coding: utf-8 -*-

from plone import api
from plone.app.layout.viewlets import ViewletBase
from plone.memoize.view import memoize

from ..config import VIEWLET_TYPES


class DocumentGeneratorLinksViewlet(ViewletBase):
    """This viewlet displays available documents to generate."""

    def available(self):
        return bool(self.get_generable_templates())

    def get_all_pod_templates(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        brains = catalog.unrestrictedSearchResults(portal_type=VIEWLET_TYPES)
        pod_templates = [self.context.unrestrictedTraverse(brain.getPath()) for brain in brains]

        return pod_templates

    @memoize
    def get_generable_templates(self):
        pod_templates = self.get_all_pod_templates()
        generable_templates = [pt for pt in pod_templates if pt.can_be_generated(self.context)]

        return generable_templates

    def get_generation_view_name(self, template, output_format):
        return 'document-generation'

    def get_links_info(self):
        base_url = self.context.absolute_url()
        links = []
        for template in self.get_generable_templates():
            for output_format in template.get_available_formats():
                title = template.Title()
                description = template.Description()
                uid = template.UID()
                link = '{base_url}/{gen_view_name}?template_uid={uid}&output_format={output_format}'.format(
                    base_url=base_url,
                    uid=uid,
                    output_format=output_format,
                    gen_view_name=self.get_generation_view_name(template, output_format)
                )
                links.append({'link': link,
                              'title': title,
                              'description': description,
                              'output_format': output_format,
                              'template_uid': uid})
        return links
