# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from collective.documentgenerator import _

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema import ValidationError


class ICollectiveDocumentGeneratorLayer(IDefaultBrowserLayer):
    """Browser layer marker interface."""


class IDemoLayer(IDefaultBrowserLayer):
    """Demo browser layer marker interface."""


class IDocumentFactory(Interface):
    """Create a persistent generated document."""

    def create(doc_file):
        """Create the object where the document 'doc_file' will be persisted."""

    def redirect(created_obj):
        """Return an http redirection after the object creation."""


class IDocumentGenerationHelper(Interface):
    """View implementing all the helpers method needed for document generation."""

    def get_value(field_name, default=None, as_utf8=False):
        """
            Return the content stored in the object field_name attribute.
            If content is None, a default can be used.
            If content is unicode and flag as_utf8 is True, it will be encoded.
        """

    def display(field_name):
        """
        Return a string representation of context's field 'field_name'.
        """

    def display_date(field_name, long_format=None, time_only=None, custom_format=None):
        """
        Return a string representation of context's date field 'field_name'.
        It uses toLocalizedTime if no custom_format is given.  A custom_format is
        a datetime strftime compatible like '%d/%m/%Y %H:%M'.
        """

    def display_voc(field_name, separator=','):
        """
        Return a join of display values of context's field 'field_name'.
        """

    def display_text_as_html(field_name):
        """
        Return the html version of the simple text field 'field_name'.
        The simple text field doesn't contain html but only text with possible carriage returns.
        """

    def display_html_as_text(field_name):
        """
        Return the plain text version of a rich text 'field_name'.
        """

    def render_xhtml(field_name):
        """
        Return the odt rendered html content of the richtext field 'field_name'.
        """

    def display_widget(fieldname, clean=True, soup=False):
        """
        Display the html widget rendering for special fields (like datagrid or progress bar).
        clean parameter: cleans some useless html parts (hidden, required).
        soup parameter: returns a soup object.
        """

    def list_voc(field_name, get='value'):
        """
        Return all display values of the context's field 'field_name' vocabulary.
        """


class IDisplayProxyObject(Interface):
    """
    Wrapper returning helper.display(field_name=attr) when trying
    to acces an attribute 'attr' of the wrapped object.
    """

    def is_field(attr_name):
        """
        Return True or False  wheter an attribute is a schema field of the object.
        To implements for each content type (dexterity and Archetypes atm).
        """


class IFieldRendererForDocument(Interface):
    """"""


class PODTemplateNotFoundError(Exception):
    """ """


class IPODTemplateCondition(Interface):
    """
    Condition object adapting a pod_template and a context.
    """

    def evaluate():
        """
        Represent the condition evaluation by returning True or False.
        """


class ITemplatesToMerge(Interface):
    """
    Adapts a pod_template to return a dict of templates to merge with appy pod.
    """

    def get():
        """
        Return the templates dict. eg: {'mytemplateid', mytemplateobj} .
        """


class IDocumentGeneratorSettings(Interface):
    """
    Settings for Document Generator.
    """


class CyclicMergeTemplatesException(Exception):
    """
    Templates to merge refers to each othert in a cyclic way.
    """


class InvalidPythonPath(ValidationError):
    __doc__ = _(u'Invalid Python path')


class InvalidUnoPath(ValidationError):
    __doc__ = _(u"Can't import python uno library with the python path")


class isNotFolderishError(Exception):
    __doc__ = _(u"Can't create a persistent document on a non folderish context.")
