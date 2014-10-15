# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IDocumentGenerationHelper
from collective.documentgenerator.interfaces import IFieldRendererForDocument

from zope.component import getMultiAdapter
from zope.interface import implements


class DocumentGenerationHelperView(object):
    """
    Base class for document generation helper view.
    """

    implements(IDocumentGenerationHelper)

    def __init__(self, context):
        """
        """
        self.context = context
        self.obj = DisplayProxyObject(context, self.display)

    def display(self, field_name, context=None):
        """To implements."""


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetypes implementation of document generation helper methods.
    """

    def display(self, field_name, context=None):
        if context is None:
            context = self.context

        field_renderer = self.get_field_renderer(field_name, context)
        display_value = field_renderer.render()

        return display_value

    def get_field_renderer(self, field_name, context):
        field = context.getField(field_name)
        widget = field.widget
        renderer = getMultiAdapter((field, widget, context), IFieldRendererForDocument)
        return renderer


class DisplayProxyObject(object):
    """
    Wrapper which will return helper.display(field_name=attr) when trying
    to acces an attribute 'attr' of context.
    """

    def __init__(self, context, display_method):
        self.context = context
        self.display = display_method

    def __getattr__(self, name):
        """
        """
        if hasattr(self.context, name):
            display_value = self.display(field_name=name)
            return display_value
        else:
            raise AttributeError
