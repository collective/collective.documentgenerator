# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IPODTemplate

from plone.dexterity.filerepresentation import ReadFileBase, DefaultWriteFile
from plone.memoize.instance import memoize

from zope.component import adapts
from zope.filerepresentation.interfaces import IRawWriteFile
from zope.interface import implements

import tempfile


class ReadFile(ReadFileBase):
    adapts(IPODTemplate)

    @property
    def mimeType(self):
        if not self.context.odt_file:
            return None
        return self.context.odt_file.contentType

    @property
    def encoding(self):
        return 'utf-8'

    @property
    def name(self):
        if not self.context.odt_file:
            return None
        return self.context.odt_file.filename

    def size(self):
        if not self.context.odt_file:
            return None
        return self.context.odt_file.getSize()

    @memoize
    def _getStream(self):
        if not self.context.odt_file:
            return None
        out = tempfile.TemporaryFile(mode='w+b')
        out.write(self.context.odt_file.data)
        out.seek(0)
        return out


class WriteFile(DefaultWriteFile):
    implements(IRawWriteFile)
    adapts(IPODTemplate)

    def close(self):
        self._message = self._parser.close()
        self._closed = True
        self.context.odt_file.data = self._message.get_payload()
