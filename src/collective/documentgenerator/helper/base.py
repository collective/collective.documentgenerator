# -*- coding: utf-8 -*-
import datetime
from collective.documentgenerator.interfaces import IDisplayProxyObject
from collective.documentgenerator.interfaces import IDocumentGenerationHelper
from plone import api
from plone.api.validation import mutually_exclusive_parameters
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import implements
from Products.CMFPlone.utils import safe_unicode


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
        raise NotImplementedError()

    def display(self, field_name, no_value=''):
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

    @mutually_exclusive_parameters('field_name', 'date')
    def display_date(self, field_name=None, date=None, long_format=None, time_only=None, custom_format=None):
        if field_name:
            date = self.get_value(field_name)

        if date is None:
            return u''

        if type(date) == datetime.date:
            date = datetime.datetime(date.year, date.month, date.day)

        if not custom_format:
            # use toLocalizedTime
            formatted_date = self.plone.toLocalizedTime(date, long_format, time_only)
        else:
            formatted_date = date.strftime(custom_format).decode('utf8')

        return safe_unicode(formatted_date)

    def display_voc(self, field_name, separator=','):
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

    @mutually_exclusive_parameters('field_name', 'text')
    def display_text_as_html(self, field_name=None, text=None):
        if field_name:
            text = self.get_value(field_name)
        return self.portal.portal_transforms.convert('web_intelligent_plain_text_to_html', text).getData()

    @mutually_exclusive_parameters('field_name', 'html')
    def display_html_as_text(self, field_name=None, html=None):
        if field_name:
            html = self.get_value(field_name)
        return self.portal.portal_transforms.convert('html_to_web_intelligent_plain_text', html).getData().strip('\n ')

    def render_xhtml(self, field_name):
        if not self.appy_renderer:
            return ''
        html_text = self.get_value(field_name)
        display = self.appy_renderer.renderXhtml(html_text)
        return display

    def display_widget(self, fieldname, clean=True, soup=False):
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

    def display_list(self, field_name, separator=', '):
        values = self.get_value(field_name)
        display = separator.join(values)
        return display

    def list(self, field_name):
        return self.get_value(field_name)

    def list_voc(self, field_name, list_keys=False, list_values=True):
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

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

    def getDGHV(self, obj):
        """ get another object 'document_generation_helper_view' view """
        view = getMultiAdapter((obj, self.request), name=u'document_generation_helper_view')
        view.appy_renderer = self.appy_renderer
        return view

    def get_state(self, title=True):
        """ Return state of object. """
        obj = self.real_context
        state = api.content.get_state(obj, default=None)
        if not state:
            return '-'
        if title:
            wtool = api.portal.get_tool('portal_workflow')
            state = wtool.getTitleForStateOnType(state, obj.portal_type)
        return state

    def context_var(self, name, default=''):
        """ Test if a context variable is defined and return it or return default """
        ctx = self.appy_renderer.contentParser.env.context
        if name in ctx:
            return ctx[name]
        else:
            return default


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
