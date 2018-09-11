# -*- coding: utf-8 -*-
from collective.documentgenerator.interfaces import IDisplayProxyObject
from collective.documentgenerator.interfaces import IDocumentGenerationHelper
from collective.documentgenerator.utils import ulocalized_time
from plone import api
from plone.api.validation import mutually_exclusive_parameters
from Products.CMFPlone.utils import safe_unicode
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import implements

import copy
import datetime
import phonenumbers


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
        proxy_obj.helper_view = self
        return proxy_obj

    def get_value(self, field_name, default=None, as_utf8=False):  # pragma: no cover
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

    def display(self, field_name, no_value=''):  # pragma: no cover
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

    @mutually_exclusive_parameters('field_name', 'date')
    def display_date(self, field_name=None, date=None, long_format=None, time_only=None, custom_format=None,
                     domain='plonelocales', target_language=None, month_lc=True, day_lc=True):
        if field_name:
            date = self.get_value(field_name)

        if date is None:
            return u''

        if type(date) == datetime.date:
            date = datetime.datetime(date.year, date.month, date.day)

        return ulocalized_time(date, long_format=long_format, time_only=time_only, custom_format=custom_format,
                               domain=domain, target_language=target_language, context=self.context,
                               request=self.request, month_lc=month_lc, day_lc=day_lc)

    @mutually_exclusive_parameters('field_name', 'phone')
    def display_phone(self, field_name=None, phone=None, country='BE', check=True, format='', pattern=''):
        """
            Return a formatted localized phone number.
            country = 2 letters country code
            check = check the validity of the given phone
            format = 'nat' or 'int'
            pattern = space replacing separators in rtl order
                      * list of 2 lists for nat and int formats => [['/', '.'], ['-', '.']]
                      * string or 2 strings (pipe separator) for nat and int formats '/.|-.'
        """
        if field_name:
            phone = self.get_value(field_name)
        if not phone:
            return u''
        try:
            number = phonenumbers.parse(phone, country)
        except phonenumbers.NumberParseException:
            return translate(u"Bad phone number: '${nb}'", domain='collective.documentgenerator',
                             mapping={'nb': phone}, context=self.request)
            return safe_unicode(phone)
        if check and not phonenumbers.is_valid_number(number):
            return translate(u"Invalid phone number: '${nb}'", domain='collective.documentgenerator',
                             mapping={'nb': phone}, context=self.request)

        def format_with_pattern(nb):
            if not pattern:
                return nb
            index = 0
            if nb.startswith('+'):
                index = 1
            if isinstance(pattern, list):
                pat = len(pattern) > index and pattern[index] or ''
            else:
                lst = pattern.split('|')
                pat = len(lst) > index and lst[index] or ''
            if not pat:
                return nb
            nbl = []
            for i, part in enumerate(nb.split()):
                nbl.append(part)
                nbl.append((pat[i:i + 1] + pat[-1:])[0])
            return ''.join(nbl[:-1])
        if format:
            ret = format_with_pattern(phonenumbers.format_number(number, format == 'int' and 1 or 2))
        elif country in phonenumbers.data._COUNTRY_CODE_TO_REGION_CODE.get(number.country_code, []):
            ret = format_with_pattern(phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.NATIONAL))
        else:
            ret = format_with_pattern(phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        return ret

    def display_voc(self, field_name, separator=','):  # pragma: no cover
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

    def display_widget(self, fieldname, clean=True, soup=False):  # pragma: no cover
        """See IDocumentGenerationHelper. To implements."""
        raise NotImplementedError()

    def display_list(self, field_name, separator=', '):
        values = self.get_value(field_name)
        display = separator.join(values)
        return display

    def list(self, field_name):
        return self.get_value(field_name)

    def list_voc(self, field_name, list_keys=False, list_values=True):  # pragma: no cover
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

    def mailing_list(self, gen_context=None):  # pragma: no cover
        """
            Return a mailing list (that will be added to generation context in "loop" view) to loop on.
            Improvement using from plone.memoize import view ?
        """
        return []

    def mailed_context(self, mailed_data):
        """ Modify current context to remove mailing_list and add mailed_data """
        try:
            new_context = copy.copy(self.appy_renderer.contentParser.env.context)
            for key in ('mailing_list', 'mailed_doc'):
                if key in new_context:
                    del new_context[key]
        except:
            return {'mailed_data': mailed_data}
        new_context['mailed_data'] = mailed_data
        return new_context

    def do_mailing(self):
        """ Check if mailing data must be replaced in template """
        ctx = self.appy_renderer.contentParser.env.context
        return 'mailed_data' in ctx


class DisplayProxyObject(object):
    """
    See IDisplayProxyObject.
    """

    implements(IDisplayProxyObject)

    def __init__(self, context, display_method):
        self.context = context
        self.display = display_method
        self.helper_view = None

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
