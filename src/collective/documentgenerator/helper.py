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

    def __init__(self, context):
        """
        """
        self.context = context
        self.obj = self._get_proxy_object(context)

    def _get_proxy_object(self, context):
        proxy_obj = getMultiAdapter((self.context, self.display), IDisplayProxyObject)
        return proxy_obj

    def display(self, field_name, context=None):
        """To implements."""


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
        """
        if self.is_field(attr_name):
            display_value = self.display(field_name=attr_name)
            return display_value

        elif hasattr(self.context, attr_name):
            return getattr(self.context, attr_name)

        else:
            raise AttributeError

    def is_field(self, attr_name):
        """To Override."""
        return False


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def display(self, field_name, context=None, no_value=''):
        if context is None:
            context = self.context

        field_renderer = self.get_field_renderer(field_name, context)
        display_value = field_renderer.render(no_value=no_value)

        return display_value

    def get_field_renderer(self, field_name, context):
        field = context.getField(field_name)
        widget = field.widget
        renderer = getMultiAdapter((field, widget, context), IFieldRendererForDocument)
        return renderer


class ATDisplayProxyObject(DisplayProxyObject):
    """
    Archetypes implementation of DisplayProxyObject.
    """

    def is_field(self, attr_name):
        is_field = bool(self.context.getField(attr_name))
        return is_field
