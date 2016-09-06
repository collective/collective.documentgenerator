# -*- coding: utf-8 -*-
"""Adapters for dexterity fields rendering."""

import datetime

from collective.documentgenerator.interfaces import IFieldRendererForDocument

from collective.excelexport.interfaces import IExportable

from zope.component import getMultiAdapter
from zope.interface import implements


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
        plone = getMultiAdapter((self.context, self.request), name=u'plone')
        if type(value) == datetime.date:
            value = datetime.datetime(value.year, value.month, value.day)
        return plone.toLocalizedTime(value)


class DexterityDatetimeExportableAdapter(DexterityExportableAdapter):

    """Adapter for collective.excelexport datetime field exportable."""

    implements(IFieldRendererForDocument)

    def render_value(self):
        """Format the date."""
        value = self.exportable.render_value(self.context)
        plone = getMultiAdapter((self.context, self.request), name=u'plone')
        return plone.toLocalizedTime(value, long_format=True)
