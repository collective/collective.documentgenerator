# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IDocumentGenerationHelper

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
        self.obj = DisplayProxyObject(self, context, self.display)

    def display(self, field_name, context=None):
        """To implements."""


class ATDocumentGenerationHelperView(DocumentGenerationHelperView):
    """
    Archetype implementation of document generation helper methods.
    """

    def display(self, field_name, context=None):
        if context is None:
            context = self.context


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
