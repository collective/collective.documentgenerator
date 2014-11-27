# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IDisplayProxyObject
from collective.documentgenerator.interfaces import IDocumentGenerationHelper
from collective.documentgenerator.interfaces import IFieldRendererForDocument

from zope.component import getMultiAdapter
from zope.interface import implements


class DocumentGenerationHelperView(object):
    """
    See IDocumentGenerationHelper.
    """

    implements(IDocumentGenerationHelper)

    def __init__(self, context, request):
        self.real_context = context
        self.request = request
        self.context = self._get_proxy_object(context)
        self.renderer = None

    def _get_proxy_object(self, context):
        proxy_obj = getMultiAdapter((self.real_context, self.display), IDisplayProxyObject)
        return proxy_obj

    def display(self, field_name, context=None):
        """See IDocumentGenerationHelper. To implements."""

    def display_date(self, field_name, context=None, format='%d/%m/%Y %H:%M'):
        """See IDocumentGenerationHelper. To implements."""

    def display_voc(self, field_name, context=None, separator=','):
        """See IDocumentGenerationHelper. To implements."""

    def display_html(self, field_name, context=None):
        """See IDocumentGenerationHelper. To implements."""

    def list_voc(self, field_name, context=None, list_keys=False, list_values=True):
        """See IDocumentGenerationHelper. To implements."""

    def _set_renderer(self, appy_renderer):
        self.renderer = appy_renderer


class DisplayProxyObject(object):
    """
    See IDisplayProxyObject.
    """

    implements(IDisplayProxyObject)

    def __init__(self, context, display_method):
        self.context = context
        self.display = display_method

    def __getattr__(self, attr_name):
        """
        Delegate field attribute access to display() method.
        """
        if self.is_field(attr_name):
            display_value = self.display(field_name=attr_name)
            return display_value

        attr = getattr(self.context, attr_name)
        return attr

    def is_field(self, attr_name):
        """To Override."""


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def display(self, field_name, context=None, no_value=''):
        if context is None:
            context = self.real_context

        field_renderer = self.get_AT_field_renderer(field_name, context)
        display_value = field_renderer.render(no_value=no_value)

        return display_value

    def get_AT_field_renderer(self, field_name, context):
        field = context.getField(field_name)
        widget = field.widget
        renderer = getMultiAdapter((field, widget, context), IFieldRendererForDocument)

        return renderer

    def display_date(self, field_name, format='%d/%m/%Y %H:%M'):
        date_field = self.context.getField(field_name)
        date = date_field.get(self.context)
        formatted_date = date.strftime(format)

        return formatted_date

    def display_voc(self, field_name, context=None, separator=', '):
        if context is None:
            context = self.real_context

        display_value = context.restrictedTraverse('@@at_utils').translate

        field = context.getField(field_name)
        voc = field.Vocabulary(context)
        raw_values = field.get(context)
        values = [display_value(voc, val) for val in raw_values]
        display = separator.join(values)

        return display

    def display_text(self, field_name, context=None):
        if not self.renderer:
            return

        if context is None:
            context = self.real_context

        html_field = self.context.getField(field_name)
        html_text = html_field.get(context)
        display = self.renderer.renderXhtml(html_text)
        return display

    def display_list(self, field_name, separator=', '):
        field = self.real_context.getField(field_name)
        values = field.get(self.real_context)
        display = separator.join(values)

        return display

    def list(self, field_name):
        field = self.real_context.getField(field_name)
        raw_values = field.getRaw(self.real_context)

        return raw_values


class ATDisplayProxyObject(DisplayProxyObject):
    """
    Archetypes implementation of DisplayProxyObject.
    """

    def is_field(self, attr_name):
        is_field = bool(self.context.getField(attr_name))
        return is_field
