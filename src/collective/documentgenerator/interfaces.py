# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema import ValidationError
from collective.documentgenerator import _


class ICollectiveDocumentGeneratorLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IDemoLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IDocumentFactory(Interface):
    """Class implementing all the helpers method needed for document generation."""

    def create(self, doc_file):
        """Create the object where the document 'doc_file' will be persisted."""

    def redirect(self, created_obj):
        """Returns an http redirection after the object creation."""


class IDocumentGenerationHelper(Interface):
    """Class implementing all the helpers method needed for document generation."""

    def display(self, field_name, context=None):
        """
        Return a string representation of context's field 'field_name'.
        """

    def display_date(self, field_name, context=None, long_format=None, time_only=None, custom_format=None):
        """
        Return a string representation of context's date field 'field_name'.
        It uses toLocalizedTime if no custom_format is given.  A custom_format is
        a datetime strftime compatible like '%d/%m/%Y %H:%M'.
        """

    def display_voc(self, field_name, context=None, separator=','):
        """
        Return a join of display values of context's field 'field_name'.
        """

    def list_voc(self, field_name, context=None, get='value'):
        """
        Return a list of display values of context's field 'field_name'.
        """


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


class ITemplatesToMerge(Interface):
    """Adapts a pod_template to return a dict of templates to merge with appy pod."""

    def get(self):
        """ Return the templates dict. eg: {'mytemplateid', mytemplateobj} ."""


class IDocumentGeneratorSettings(Interface):
    """
    Settings for Document Generator
    """


class CyclicMergeTemplatesException(Exception):
    """
    Thrown when templates to merge refers to each othert in a cyclic way.
    """


class InvalidPythonPath(ValidationError):
    __doc__ = _(u"Invalid Python path")


class InvalidUnoPath(ValidationError):
    __doc__ = _(u"Can't import python uno library with the python path")


class isNotFolderishError(Exception):
    __doc__ = _(u"Can't create a persistent document on a non foldersih context.")
