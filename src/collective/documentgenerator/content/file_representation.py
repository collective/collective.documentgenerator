# -*- coding: utf-8 -*-

from plone.dexterity.filerepresentation import ReadFileBase, DefaultWriteFile
from plone.dexterity.utils import iterSchemata
from plone.memoize.instance import memoize
from plone.rfc822.interfaces import IPrimaryField

from zope.filerepresentation.interfaces import IRawWriteFile
from zope.interface import implements
from zope.schema import getFieldsInOrder

import tempfile


class PrimaryFileBase(object):

    @memoize
    def _get_primary_field(self):
        for schema in iterSchemata(self.context):
            for field_name, field in getFieldsInOrder(schema):
                if IPrimaryField.providedBy(field):
                    primary_field = getattr(self.context, field_name)
                    return primary_field


class ReadFile(ReadFileBase, PrimaryFileBase):

    @property
    def mimeType(self):
        primary_field = self._get_primary_field()
        if not primary_field:
            return None
        return primary_field.contentType

    @property
    def encoding(self):
        return 'utf-8'

    @property
    def name(self):
        primary_field = self._get_primary_field()
        if not primary_field:
            return None
        return primary_field.filename

    def size(self):
        primary_field = self._get_primary_field()
        if not primary_field:
            return None
        return primary_field.getSize()

    @memoize
    def _getStream(self):
        primary_field = self._get_primary_field()
        if not primary_field:
            return None
        out = tempfile.TemporaryFile(mode='w+b')
        out.write(primary_field.data)
        out.seek(0)
        return out


class WriteFile(DefaultWriteFile, PrimaryFileBase):
    implements(IRawWriteFile)

    def close(self):
        self._message = self._parser.close()
        self._closed = True
        primary_field = self._get_primary_field()
        primary_field.data = self._message.get_payload()
