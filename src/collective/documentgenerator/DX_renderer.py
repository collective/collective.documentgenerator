# -*- coding: utf-8 -*-
"""Adapters for dexterity fields rendering."""

from collective.documentgenerator.interfaces import IFieldRendererForDocument
from collective.excelexport.interfaces import IExportable
from zope.component import getMultiAdapter
from zope.interface import implementer

import datetime


@implementer(IFieldRendererForDocument)
class DexterityExportableAdapter(object):

    """Adapter for collective.excelexport exportables."""

    def __init__(self, field, context, request):
        self.field = field
        self.context = context
        self.request = request
        self.exportable = getMultiAdapter(
            (field, context, request), IExportable)

    def render_value(self):
        """Just delegate the rendering to the exportable."""
        return self.exportable.render_value(self.context)


@implementer(IFieldRendererForDocument)
class DexterityDateExportableAdapter(DexterityExportableAdapter):

    """Adapter for collective.excelexport date field exportable."""

    def render_value(self):
        """Format the date."""
        value = self.exportable.render_value(self.context)
        plone = getMultiAdapter((self.context, self.request), name=u'plone')
        if type(value) == datetime.date:
            value = datetime.datetime(value.year, value.month, value.day)
        return plone.toLocalizedTime(value)


@implementer(IFieldRendererForDocument)
class DexterityDatetimeExportableAdapter(DexterityExportableAdapter):

    """Adapter for collective.excelexport datetime field exportable."""

    def render_value(self):
        """Format the date."""
        value = self.exportable.render_value(self.context)
        plone = getMultiAdapter((self.context, self.request), name=u'plone')
        return plone.toLocalizedTime(value, long_format=True)
