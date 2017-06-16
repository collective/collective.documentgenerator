# -*- coding: utf-8 -*-

from Products.CMFCore.interfaces import IFolderish

from collective.documentgenerator.interfaces import IDocumentFactory
from collective.documentgenerator.interfaces import isNotFolderishError

from plone import api
from plone.namedfile.file import NamedBlobFile

from zope.interface import implements

import mimetypes


class ATCTFileDocumentFactory(object):
    """
    Factory to create an ATCT File (Archetypes) object persisting a generated document.
    """

    implements(IDocumentFactory)

    def __init__(self, context):
        self.context = context

    def create(self, doc_file, title='document', extension='odt'):

        if not IFolderish.providedBy(self.context):
            raise isNotFolderishError

        container = self.context

        document = api.content.create(
            type='File',
            title=title,
            file=doc_file,
            container=container,
        )

        filename = u'{}.{}'.format(title, extension)

        document.getFile().setFilename(filename)
        document.getFile().setContentType(mimetypes.guess_type(filename)[0])

        return document


class PACTFileDocumentFactory(object):
    """
    Factory to create a PACT File (dexterity) object persisting a generated document.
    """

    implements(IDocumentFactory)

    def __init__(self, context):
        self.context = context

    def create(self, doc_file, title='document', extension='odt'):

        if not IFolderish.providedBy(self.context):
            raise isNotFolderishError

        container = self.context
        filename = u'{}.{}'.format(title, extension)
        content_type = mimetypes.guess_type(filename)[0]
        file_content = NamedBlobFile(
            data=doc_file,
            contentType=content_type,
            filename=filename,
        )

        document = api.content.create(
            type='File',
            title=title,
            file=file_content,
            container=container,
        )
        return document
