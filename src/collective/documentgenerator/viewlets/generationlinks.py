# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IGenerablePODTemplates
from plone.app.layout.viewlets import ViewletBase
from plone.memoize.view import memoize
from zope.component import getAdapter


class DocumentGeneratorLinksViewlet(ViewletBase):
    """This viewlet displays available documents to generate."""

    def available(self):
        return bool(self.get_generable_templates())

    @memoize
    def get_generable_templates(self):
        adapter = getAdapter(self.context, IGenerablePODTemplates)
        generable_templates = adapter.get_generable_templates()
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
                infos = {'link': link,
                         'title': title,
                         'description': description,
                         'output_format': output_format,
                         'template_uid': uid,
                         'template': template}
                infos.update(self.add_extra_links_info(template, infos))
                links.append(infos)
        return links

    def add_extra_links_info(self, template, infos):
        """This method is made to be overrided and ease adding extra infos
           to the list of dicts returned by self.get_links_info.
           It needs to returns a dict that will update data stored in infos."""
        return {}
