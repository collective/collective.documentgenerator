# -*- coding: utf-8 -*-
"""Adapters for dexterity fields rendering."""

from collective.documentgenerator.interfaces import IFieldRendererForDocument
from collective.documentgenerator.utils import unescape_vocabulary_title
from collective.excelexport.interfaces import IExportable
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import ICollection

import datetime


def renders_vocabulary_titles(field):
    """Is the value rendered for this field a vocabulary term title ?"""
    if IChoice.providedBy(field):
        return True
    return ICollection.providedBy(field) and IChoice.providedBy(field.value_type)


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
        value = self.exportable.render_value(self.context)
        if renders_vocabulary_titles(self.field):
            value = unescape_vocabulary_title(value)
        return value


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
