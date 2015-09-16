# -*- coding: utf-8 -*-

from AccessControl import Unauthorized

from Products.Five import BrowserView

from StringIO import StringIO

from collective.documentgenerator import config
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.interfaces import CyclicMergeTemplatesException
from collective.documentgenerator.interfaces import IDocumentFactory
from collective.documentgenerator.interfaces import PODTemplateNotFoundError

from plone import api

from zope.component import queryAdapter

import appy.pod.renderer
import mimetypes
import os
import tempfile


class DocumentGenerationView(BrowserView):
    """
    Document generation with appy.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.pod_template = self.get_pod_template()
        return self.generate_and_download_doc()

    def generate_and_download_doc(self):
        doc, doc_name = self.generate_doc()
        self.set_header_response(doc_name)
        return doc

    def generate_doc(self):
        """
        Generate a document and returns it as a downloadable file.
        """
        if not self.pod_template.can_be_generated(self.context):
            raise Unauthorized('You are not allowed to generate this document.')

        self.check_cyclic_merges(self.pod_template)

        document_path = self.recursive_generate_doc(self.pod_template)

        rendered_document = open(document_path, 'rb')
        rendered = rendered_document.read()
        rendered_document.close()
        os.remove(document_path)

        filename = u'{}.{}'.format(self.pod_template.title, self.get_generation_format())

        return rendered, filename

    def recursive_generate_doc(self, pod_template, force_odt=False):

        sub_templates = pod_template.get_templates_to_merge()
        sub_documents = {}
        for context_name, sub_pod in sub_templates.iteritems():
            sub_documents[context_name] = self.recursive_generate_doc(sub_pod, force_odt=True)

        document_template = pod_template.get_file()
        file_type = self.get_generation_format()

        document_path = self.render_document(document_template, file_type, sub_documents, force_odt=force_odt)

        return document_path

    def get_pod_template(self):
        template_uid = self.get_pod_template_uid()
        catalog = api.portal.get_tool('portal_catalog')

        template_brains = catalog.unrestrictedSearchResults(
            object_provides=IPODTemplate.__identifier__,
            UID=template_uid
        )
        if not template_brains:
            raise PODTemplateNotFoundError(
                "Couldn't find POD template with UID '{}'".format(template_uid)
            )

        template_path = template_brains[0].getPath()
        pod_template = self.context.unrestrictedTraverse(template_path)
        return pod_template

    def get_pod_template_uid(self):
        template_uid = self.request.get('doc_uid', None)
        return template_uid

    def get_generation_format(self):
        """
        Get the format we want to generate the template in.
        If 'output_format' found in the REQUEST is not an available format, we raise.
        """
        output_format = self.request.get('output_format')
        if not output_format:
            raise Exception("'output_format' was not found in the REQUEST!")
        if output_format not in self.pod_template.get_available_formats():
            raise Exception("Asked output format '{0}' "
                            "is not available for template '{1}'!".format(output_format,
                                                                          self.pod_template.getId()))
        return output_format

    def render_document(self, document_obj, file_type, sub_documents, force_odt=False):
        temp_filename = tempfile.mktemp('.{0}'.format(force_odt and 'odt' or self.get_generation_format()))

        # Prepare rendering context
        helper_view = self.get_generation_context_helper()

        generation_context = self.get_generation_context(helper_view)
        generation_context.update(sub_documents)

        renderer = appy.pod.renderer.Renderer(
            StringIO(document_obj.data),
            generation_context,
            temp_filename,
            pythonWithUnoPath=config.get_uno_path(),
        )

        # it is only now that we can initialize helper view's appy pod renderer
        helper_view._set_appy_renderer(renderer)

        renderer.run()

        return temp_filename

    def get_generation_context(self, helper_view):
        generation_context = self.get_base_generation_context()
        generation_context.update(
            {
                'context': getattr(helper_view, 'context', None),
                'view': helper_view
            }
        )
        return generation_context

    def get_base_generation_context(self):
        return {}

    def get_generation_context_helper(self):
        helper = self.context.unrestrictedTraverse('@@document_generation_helper_view')
        return helper

    def set_header_response(self, filename):
        # Tell the browser that the resulting page contains ODT
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader(
            'Content-disposition',
            u'inline;filename="{}"'.format(filename).encode('utf-8')
        )

    def check_cyclic_merges(self, pod_template):
        def traverse_check(pod_template, path):

            if pod_template in path:
                path.append(pod_template)
                start_cycle = path.index(pod_template)
                start_msg = ' --> '.join(
                    ['"{}" {}'.format(t.Title(), '/'.join(t.getPhysicalPath())) for t in path[:start_cycle]]
                )
                cycle_msg = ' <--> '.join(
                    ['"{}" {}'.format(t.Title(), '/'.join(t.getPhysicalPath())) for t in path[start_cycle:]]
                )
                msg = '{} -> CYCLE:\n{}'.format(start_msg, cycle_msg)
                raise CyclicMergeTemplatesException(msg)

            new_path = list(path)
            new_path.append(pod_template)

            sub_templates = pod_template.get_templates_to_merge()

            for name, sub_template in sub_templates.iteritems():
                traverse_check(sub_template, new_path)

        traverse_check(pod_template, [])


class PersistentDocumentGenerationView(DocumentGenerationView):
    """
    """

    def __call__(self):
        super(PersistentDocumentGenerationView, self).__call__()
        persisted_doc = self.generate_persistent_doc()
        self.redirects(persisted_doc)

    def generate_persistent_doc(self):
        """
        Generate a document, create a 'File' on the context with the generated document
        and redirect to the created File.
        """

        doc, doc_name = self.generate_doc()

        title, extension = doc_name.split('.')

        factory = queryAdapter(self.context, IDocumentFactory)

        #  Bypass any File creation permission of the user. If the user isnt
        #  supposed to save generated document on the site, then its the permission
        #  to call the generation view that should be changed.
        with api.env.adopt_roles(['Manager']):
            persisted_doc = factory.create(doc_file=doc, title=title, extension=extension)

        return persisted_doc

    def redirects(self, persisted_doc):
        self.set_header_response(persisted_doc.getFile().filename)
        response = self.request.response
        return response.redirect(persisted_doc.absolute_url() + '/external_edit')
