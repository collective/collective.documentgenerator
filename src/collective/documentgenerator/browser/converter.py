# -*- coding: utf-8 -*-
from collective.documentgenerator.utils import convert_and_save_odt
from collective.documentgenerator.utils import convert_odt
from plone.namedfile.file import NamedBlobFile
from Products.Five import BrowserView

import mimetypes


class DocumentConvertView(BrowserView):
    """A view to convert document from odt to pdf and download it"""

    def get_params(self):
        fmt = self.request.get('format', 'pdf')
        output_name = self.request.get('output_name', "untitled.{}".format(fmt))
        if not output_name and isinstance(self.context.file, NamedBlobFile):
            output_name = self.context.file.filename.replace('.odt', '.{}'.format(fmt))
        return output_name, fmt

    def __call__(self):
        output_name, fmt = self.get_params()
        converted_filename, converted_file = convert_odt(self.context.file, output_name, fmt=fmt)

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
        output_name, fmt = self.get_params()
        convert_and_save_odt(self.context.file, self.context.aq_parent, self.context.portal_type, output_name, fmt=fmt)

        self.request.response.redirect(self.context.aq_parent.absolute_url())
