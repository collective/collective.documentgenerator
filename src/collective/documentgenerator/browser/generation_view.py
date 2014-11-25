# -*- coding: utf-8 -*-

from AccessControl import Unauthorized

from Products.Five import BrowserView

from StringIO import StringIO

from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.interfaces import IDocumentFactory
from collective.documentgenerator.interfaces import IDocumentGenerationHelper
from collective.documentgenerator.interfaces import PODTemplateNotFoundError

from imio.helpers.security import call_as_super_user

from plone import api

from zope.component import queryAdapter
from zope.component import queryMultiAdapter

import appy.pod.renderer
import mimetypes
import os
import tempfile
import time


class DocumentGenerationView(BrowserView):
    """
    Document generation with appy.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return self.generate_and_download_doc()

    def generate_and_download_doc(self):
        doc, doc_name = self.generate_doc()
        self.set_header_response(doc_name)
        return doc

    def generate_doc(self):
        """
        Generate a document and returns it as a downloadable file.
        """
        # The user calling the generation action is not always allowed to access
        # the PODtemplates, so we use call_as_super_user to be sure to find
        # them..
        pod_template = call_as_super_user(self.get_pod_template)

        if not pod_template.can_be_generated(self.context):
            raise Unauthorized('You are not allowed to generate this document.')

        document_template = pod_template.get_file()
        file_type = self.get_generation_format()

        rendered_document = self.render_document(document_template, file_type)
        filename = '{}.{}'.format(pod_template.title, file_type)

        return rendered_document, filename

    def get_pod_template(self):
        template_uid = self.get_pod_template_uid()
        catalog = api.portal.get_tool('portal_catalog')

        template_brains = catalog(object_provides=IPODTemplate.__identifier__, UID=template_uid)
        if not template_brains:
            raise PODTemplateNotFoundError(
                "Couldn't find POD template with UID '{}'".format(template_uid)
            )

        pod_template = template_brains[0].getObject()
        return pod_template

    def get_pod_template_uid(self):
        template_uid = self.request.get('doc_uid', None)
        return template_uid

    def get_generation_format(self):
        generation_format = self.request.get('output_format', 'odt')
        return generation_format

    def render_document(self, document_obj, file_type):
        temp_filename = '%s/%s_%f.%s' % (tempfile.gettempdir(), document_obj.size, time.time(), file_type)
        # Prepare rendering context
        dgm = self.get_generation_context_helper()
        generation_context = {
            'context': getattr(dgm, 'context', None),
            'view': dgm
        }
        renderer = appy.pod.renderer.Renderer(
            StringIO(document_obj.data),
            generation_context,
            temp_filename,
            pythonWithUnoPath='/usr/bin/python',
            forceOoCall=True,
        )

        renderer.run()

        rendered_document = open(temp_filename, 'rb')
        rendered = rendered_document.read()
        rendered_document.close()
        os.remove(temp_filename)

        return rendered

    def get_generation_context_helper(self):
        helper = queryAdapter(self.context, IDocumentGenerationHelper)
        return helper

    def set_header_response(self, filename):
        # Tell the browser that the resulting page contains ODT
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader('Content-disposition', 'inline;filename="{}"'.format(filename))


class PersistentDocumentGenerationView(DocumentGenerationView):
    """
    """

    def __call__(self):
        self.generate_persistant_doc()

    def generate_persistant_doc(self):
        """
        Generate a document, create a 'File' on the context with the generated document
        and redirect to the created File.
        """

        doc, doc_name = self.generate_doc()

        title, extension = doc_name.split('.')

        factory = queryMultiAdapter((self.context, self.request), IDocumentFactory)

        #  Bypass any File creation permission of the user. If the user isnt
        #  supposed to save generated document on the site, then its the permission
        #  to call the generation view that should be changed.
        call_as_super_user(
            factory.create,
            doc_file=doc,
            title=title,
            extension=extension
        )
