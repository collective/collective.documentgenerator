# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IDisplayProxyObject
from collective.documentgenerator.interfaces import IDocumentGenerationHelper

from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import implements


class DocumentGenerationHelperView(object):
    """
    See IDocumentGenerationHelper.
    """

    implements(IDocumentGenerationHelper)

    def __init__(self, context, request):
        super(DocumentGenerationHelperView, self).__init__(context, request)
        self.real_context = context
        self.request = request
        self.context = self._get_proxy_object()
        self.appy_renderer = None
        self.plone = getMultiAdapter((context, request), name=u'plone')
        self.plone_portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
        self.portal = self.plone_portal_state.portal()

    def _get_proxy_object(self):
        proxy_obj = getMultiAdapter((self.real_context, self.display), IDisplayProxyObject)
        return proxy_obj

    def get_value(self, field_name, default=None, as_utf8=False):
        """See IDocumentGenerationHelper. To implements."""

    def display(self, field_name, no_value=''):
        """See IDocumentGenerationHelper. To implements."""

    def display_date(self, field_name, long_format=None, time_only=None, custom_format=None):
        """See IDocumentGenerationHelper. To implements."""

    def display_voc(self, field_name, separator=','):
        """See IDocumentGenerationHelper. To implements."""

    def display_html(self, field_name):
        """See IDocumentGenerationHelper. To implements."""

    def display_widget(self, fieldname, clean=True, soup=False):
        """See IDocumentGenerationHelper. To implements."""

    def list_voc(self, field_name, list_keys=False, list_values=True):
        """See IDocumentGenerationHelper. To implements."""

    def _set_appy_renderer(self, appy_renderer):
        self.appy_renderer = appy_renderer

    def translate(self, msgid, domain='plone', mapping={}, target_language=None, default=None):
        """Let's translate a given msgid in given domain."""
        return translate(msgid,
                         domain,
                         mapping=mapping,
                         context=self.request,
                         target_language=target_language,
                         default=default)

    def getDGHV(self, obj, appy_rdr=None):
        """ get another object 'document_generation_helper_view' view """
        view = getMultiAdapter((obj, self.request), name=u'document_generation_helper_view')
        if appy_rdr is not None:
            view.appy_renderer = appy_rdr
        return view


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
