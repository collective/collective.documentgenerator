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
    Document generation view.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, template_uid='', output_format=''):
        pod_template, output_format = self._get_base_args(template_uid, output_format)
        return self.generate_and_download_doc(pod_template, output_format)

    def _get_base_args(self, template_uid, output_format):
        template_uid = template_uid or self.get_pod_template_uid()
        pod_template = self.get_pod_template(template_uid)
        output_format = output_format or self.get_generation_format()
        if not output_format:
            raise Exception("No 'output_format' found to generate this document")

        return pod_template, output_format

    def generate_and_download_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template' and return it as a downloadable file.
        """
        doc, doc_name = self._generate_doc(pod_template, output_format)
        self._set_header_response(doc_name)
        return doc

    def _generate_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template'.
        """
        if not pod_template.can_be_generated(self.context):
            raise Unauthorized('You are not allowed to generate this document.')

        if output_format not in pod_template.get_available_formats():
            raise Exception(
                "Asked output format '{0}' "
                "is not available for template '{1}'!".format(
                    output_format,
                    pod_template.getId()
                )
            )

        # subtemplates should not refer to each other in a cyclic way.
        self._check_cyclic_merges(pod_template)

        # Recursive generation of the document and all its subtemplates.
        document_path = self._recursive_generate_doc(pod_template, output_format)

        rendered_document = open(document_path, 'rb')
        rendered = rendered_document.read()
        rendered_document.close()
        os.remove(document_path)

        filename = u'{}.{}'.format(pod_template.title, output_format)

        return rendered, filename

    def _recursive_generate_doc(self, pod_template, output_format):
        """
        Generate a document recursively by starting to generate all its
        subtemplates before merging them in the final document.
        Return the file path of the generated document.
        """
        sub_templates = pod_template.get_templates_to_merge()
        sub_documents = {}
        for context_name, sub_pod in sub_templates.iteritems():
            # Force the subtemplate output_format to 'odt' because appy.pod
            # can only merge documents in this format.
            sub_documents[context_name] = self._recursive_generate_doc(
                pod_template=sub_pod,
                output_format='odt'
            )

        document_template = pod_template.get_file()

        document_path = self._render_document(document_template, output_format, sub_documents)

        return document_path

    def get_pod_template(self, template_uid):
        """
        Return the default PODTemplate that will be used when calling
        this view.
        """
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
        template_uid = self.request.get('template_uid', None)
        return template_uid

    def get_generation_format(self):
        """
        Return the default document output format that will be used
        when calling this view.
        """
        output_format = self.request.get('output_format')
        return output_format

    def _render_document(self, document_template, output_format, sub_documents):
        """
        Render a single document of type 'output_format' using the odt file
        'document_template' as the generation template.
        Subdocuments is a dictionnary of previously generated subtemplate
        that will be merged into the current generated document.
        """
        temp_filename = tempfile.mktemp('.{extension}'.format(extension=output_format))

        # Prepare rendering context
        helper_view = self.get_generation_context_helper()
        generation_context = self._get_generation_context(helper_view)
        # enrich the generation context with previously generated documents
        generation_context.update(sub_documents)

        renderer = appy.pod.renderer.Renderer(
            StringIO(document_template.data),
            generation_context,
            temp_filename,
            pythonWithUnoPath=config.get_uno_path(),
        )

        # it is only now that we can initialize helper view's appy pod renderer
        helper_view._set_appy_renderer(renderer)

        renderer.run()

        return temp_filename

    def _get_generation_context(self, helper_view):
        """
        Return the generation context for the current document.
        """
        generation_context = self.get_base_generation_context()
        generation_context.update(
            {
                'context': getattr(helper_view, 'context', None),
                'view': helper_view
            }
        )
        return generation_context

    def get_base_generation_context(self):
        """
        Override this method to provide your own generation context.
        """
        return {}

    def get_generation_context_helper(self):
        """
        Return the default helper view used for document generation.
        """
        helper = self.context.unrestrictedTraverse('@@document_generation_helper_view')
        return helper

    def _set_header_response(self, filename):
        """
        Tell the browser that the resulting page contains ODT.
        """
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader(
            'Content-disposition',
            u'inline;filename="{}"'.format(filename).encode('utf-8')
        )

    def _check_cyclic_merges(self, pod_template):
        """
        Check if the template 'pod_template' has subtemplates referring to each
        other in a cyclic way.
        """
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
    Persistent document generation view.
    """

    def __call__(self, template_uid='', output_format=''):
        pod_template, output_format = self._get_base_args(template_uid, output_format)
        persisted_doc = self.generate_persistent_doc(pod_template, output_format)
        self.redirects(persisted_doc)

    def generate_persistent_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template' and persist it by creating a File containing the
        generated document on the current context.
        """

        doc, doc_name = self._generate_doc(pod_template, output_format)

        title, extension = doc_name.split('.')

        factory = queryAdapter(self.context, IDocumentFactory)

        #  Bypass any File creation permission of the user. If the user isnt
        #  supposed to save generated document on the site, then its the permission
        #  to call the generation view that should be changed.
        with api.env.adopt_roles(['Manager']):
            persisted_doc = factory.create(doc_file=doc, title=title, extension=extension)

        return persisted_doc

    def redirects(self, persisted_doc):
        """
        Redirects to the created document.
        """
        self._set_header_response(persisted_doc.getFile().filename)
        response = self.request.response
        return response.redirect(persisted_doc.absolute_url() + '/external_edit')
