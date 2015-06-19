# -*- coding: utf-8 -*-
"""Adapters for dexterity fields rendering."""
from zope.component import getMultiAdapter
from zope.interface import implements

from collective.excelexport.interfaces import IExportable

from collective.documentgenerator.interfaces import IFieldRendererForDocument


class DexterityExportableAdapter(object):

    """Adapter for collective.excelexport exportables."""

    implements(IFieldRendererForDocument)

    def __init__(self, field, context, request):
        self.field = field
        self.context = context
        self.request = request
        self.exportable = getMultiAdapter(
            (field, context, request), IExportable)

    def render_value(self):
        """Just delegate the rendering to the exportable."""
        return self.exportable.render_value(self.context)


class DexterityDateExportableAdapter(DexterityExportableAdapter):

    """Adapter for collective.excelexport date field exportable."""

    implements(IFieldRendererForDocument)

    def render_value(self):
        """Format the date."""
        value = self.exportable.render_value(self.context)
        return value.strftime('%d/%m/%Y %H:%M')
