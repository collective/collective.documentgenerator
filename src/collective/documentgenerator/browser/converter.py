# -*- coding: utf-8 -*-

from appy.pod.lo_pool import LoPool
from appy.pod.renderer import Renderer
from collective.documentgenerator import config
from collective.documentgenerator.utils import create_temporary_file
from collective.documentgenerator.utils import remove_tmp_file
from plone import api
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobFile
from Products.Five import BrowserView
from StringIO import StringIO

import mimetypes


def convert_odt_to_pdf(context, **kwargs):
    """
    Convert an odt file to pdf using appy.pod
    kwargs are passed to the renderer, i.e pdfOptions='ExportNotes=True;SelectPdfVersion=1'
    """
    lo_pool = LoPool.get(
        python=config.get_uno_path(),
        server=config.get_oo_server(),
        port=config.get_oo_port_list(),
    )

    dummy_template = api.portal.get()["templates"]["om"]["main"]
    renderer = Renderer(
        StringIO(dummy_template.get_file().data),
        context.aq_parent,
        "dummy.pdf",
        **kwargs,
    )

    temp_file = create_temporary_file(context.file, '.odt')
    lo_pool(renderer, temp_file.name, "pdf")
    remove_tmp_file(temp_file.name)
    converted_filename = temp_file.name.replace('.odt', '.pdf')
    converted_file = open(converted_filename, 'rb').read()
    remove_tmp_file(converted_filename)

    return converted_filename, converted_file


class DocumentConvertView(BrowserView):
    """A view to convert document from odt to pdf and download it"""

    def __call__(self):
        converted_filename, converted_file = convert_odt_to_pdf(self.context)
        
        # Set headers
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(converted_filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader(
            'Content-disposition',
            u'inline;filename="{}"'.format(converted_filename).encode('utf-8')
        )

        return converted_file


class PersistentDocumentConvertView(BrowserView):
    """A view to convert document from odt to pdf and save it on the parent"""

    def __call__(self):
        _, converted_file = convert_odt_to_pdf(self.context)
        file_object = NamedBlobFile(converted_file, filename=self.context.file.filename.replace('.odt', '.pdf'))
        createContentInContainer(self.context.aq_parent, self.context.portal_type, title=self.context.title.replace('.odt', '.pdf'), file=file_object)

        self.request.response.redirect(self.context.aq_parent.absolute_url())
