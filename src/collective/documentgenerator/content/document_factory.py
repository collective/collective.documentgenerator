# -*- coding: utf-8 -*-

from Products.CMFCore.interfaces import IFolderish

from collective.documentgenerator.interfaces import IDocumentFactory

from plone import api

from zope.interface import implements

import mimetypes


class FileDocumentFactory(object):
    """
    Factory to create a File object persisting a generated document.
    """

    implements(IDocumentFactory)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def create(self, doc_file, title='document', extension='odt'):

        if IFolderish.providedBy(self.context):
            container = self.context
        else:
            container = self.context.aq_parent

        obj = api.content.create(
            type='File',
            title=title,
            file=doc_file,
            container=container,
        )

        filename = u'{}.{}'.format(title, extension)

        obj.getFile().setFilename(filename)
        obj.getFile().setContentType(mimetypes.guess_type(filename)[0])

        return obj.getFile()
