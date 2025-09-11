# -*- coding: utf-8 -*-

from collective.documentgenerator.utils import convert_odt
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobFile
from Products.Five import BrowserView

import mimetypes


class DocumentConvertView(BrowserView):
    """A view to convert document from odt to pdf and download it"""

    def convert(self):
        format = self.request.get('format', 'pdf')
        output_name = self.request.get('output_name', None)
        if not output_name and isinstance(self.context.file, NamedBlobFile):
            output_name = self.context.file.filename.replace('.odt', '.{}'.format(format))
        converted_filename, converted_file = convert_odt(self.context.file, fmt=format)
        if output_name:
            converted_filename = output_name

        return converted_filename, converted_file

    def __call__(self):
        converted_filename, converted_file = self.convert()

        # Set headers
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(converted_filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader(
            'Content-disposition',
            u'inline;filename="{}"'.format(converted_filename).encode('utf-8')
        )

        return converted_file


class PersistentDocumentConvertView(DocumentConvertView):
    """A view to convert document from odt to pdf and save it on the parent"""

    def __call__(self):
        converted_filename, converted_file = self.convert()
        file_object = NamedBlobFile(converted_file, filename=converted_filename)
        createContentInContainer(
            self.context.aq_parent,
            self.context.portal_type,
            title=converted_filename,
            file=file_object)

        self.request.response.redirect(self.context.aq_parent.absolute_url())
