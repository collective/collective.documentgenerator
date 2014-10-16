# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface

from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICollectiveDocumentgeneratorLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IDocumentGenerationHelper(Interface):
    """Class implementing all the helpers method needed for document generation."""


class IDisplayProxyObject(Interface):
    """
    Wrapper which will return helper.display(field_name=attr) when trying
    to acces an attribute 'attr' of context.
    """

    def is_field(self, attr_name):
        """
        Return True or False  wheter an attribute is a schema field of the object.
        To be implemented for each content type (dexterity and Archetypes atm).
        """


class IFieldRendererForDocument(Interface):
    """"""


class PODTemplateNotFoundError(Exception):
    """ """


class IPODTemplateCondition(Interface):
    """Condition object adapting a pod_template and a context."""

    def evaluate(self):
        """Represent the condition evaluation by returning True or False."""
