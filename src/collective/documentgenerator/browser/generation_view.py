# -*- coding: utf-8 -*-

from AccessControl import Unauthorized

from Products.Five import BrowserView

from StringIO import StringIO

from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.interfaces import PODTemplateNotFoundError

from imio.helpers.os_helpers import get_tmp_folder
from imio.helpers.security import call_as_super_user

from plone import api

from zope.component import queryMultiAdapter

import appy.pod.renderer
import os
import time


class DocumentGenerationView(BrowserView):
    """
    Document generation with appy.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return self.generate_doc()

    def generate_doc(self):
        # The user calling the generation action is not always allowed to access
        # the PODtemplates, so we use call_as_super_user to be sure to find
        # them..
        pod_template = call_as_super_user(self.get_pod_template)

        if not pod_template.can_be_generated(self.context):
            raise Unauthorized('You are not allowed to generate this document.')

        document_template = pod_template.get_file()
        file_type = self.get_generation_mimetype()

        rendered_document = self.render_document(document_template, file_type)
        self.set_header_response(file_type)
        return rendered_document

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

    def get_generation_mimetype(self):
        mimetype = self.request.get('output_format', 'odt')
        return mimetype

    def render_document(self, document_obj, file_type):
        temp_filename = '%s/%s_%f.%s' % (get_tmp_folder(), document_obj.size, time.time(), file_type)
        # Prepare rendering context
        dgm = self.get_generation_context_helper()
        generation_context = {'self': self.context, 'view': dgm}
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
        helper = queryMultiAdapter((self.context, self.request), name=u'document-generation-methods')
        return helper

    def set_header_response(self, file_type):
        # Tell the browser that the resulting page contains ODT
        response = self.request.RESPONSE
        response.setHeader('Content-type', 'application/%s' % file_type)
        response.setHeader('Content-disposition', 'inline;filename="%s.%s"' % (self.context.id, file_type))
