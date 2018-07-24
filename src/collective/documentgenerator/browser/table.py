# -*- coding: utf-8 -*-
"""Define tables and columns."""

from collective.documentgenerator import _
from plone import api
from Products.CMFPlone import PloneMessageFactory as PMF
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_unicode
from z3c.table.column import Column
from z3c.table.column import LinkColumn
from z3c.table.table import Table
from zope.cachedescriptors.property import CachedProperty
from zope.component import getMultiAdapter
from zope.i18n import translate

import html
import os


class TemplatesTable(Table):

    """Table that displays templates info."""

    cssClassEven = u'even'
    cssClassOdd = u'odd'
    cssClasses = {'table': 'listing nosort templates-listing icons-on'}

    # ?table-batchSize=10&table-batchStart=30
    batchSize = 200
    startBatchingAt = 200
    sortOn = None
    results = []

    def __init__(self, context, request):
        super(TemplatesTable, self).__init__(context, request)
        self.portal = api.portal.getSite()
        self.context_path = self.context.absolute_url_path()
        self.context_path_level = len(self.context_path.split('/'))
        self.paths = {'.': '-'}

    @CachedProperty
    def wtool(self):
        return api.portal.get_tool('portal_workflow')

    @CachedProperty
    def portal_url(self):
        return api.portal.get().absolute_url()

    @CachedProperty
    def values(self):
        return self.results


try:
    from collective.eeafaceted.z3ctable.columns import CheckBoxColumn as cbc
    cbc_base = cbc
except ImportError:
    cbc_base = Column


class CheckBoxColumn(cbc_base):
    """ checkbox column used for batch actions """

    cssClasses = {'td': 'select-column'}
    weight = 5

    def getValue(self, item):
        return item.UID()


class TitleColumn(LinkColumn):

    """Column that displays title."""

    header = PMF("Title")
    weight = 10
    cssClasses = {'td': 'title-column'}
    i_cache = {}

    def _icons(self, item):
        """See docstring in interfaces.py."""
        if item.portal_type not in self.i_cache:
            icon_link = ''
            purl = api.portal.get_tool('portal_url')()
            typeInfo = api.portal.get_tool('portal_types')[item.portal_type]
            if typeInfo.icon_expr:
                # we assume that stored icon_expr is like string:${portal_url}/myContentIcon.png
                # or like string:${portal_url}/++resource++imio.dashboard/dashboardpodtemplate.png
                contentIcon = '/'.join(typeInfo.icon_expr.split('/')[1:])
                title = translate(typeInfo.title, domain=typeInfo.i18n_domain, context=self.request)
                icon_link = u'<img title="%s" src="%s/%s" />' % (safe_unicode(title), purl, contentIcon)
            self.i_cache[item.portal_type] = icon_link
        return self.i_cache[item.portal_type]

    def getLinkCSS(self, item):
        return ' class="pretty_link state-%s"' % (api.content.get_state(obj=item))

    def getLinkContent(self, item):
        return u'<span class="pretty_link_icons">%s</span>' \
            u'<span class="pretty_link_content">%s</span>' % (self._icons(item), safe_unicode(item.title))


class PathColumn(LinkColumn):

    """Column that displays path."""

    header = _("Path")
    weight = 20
    cssClasses = {'td': 'path-column'}
    linkTarget = '_blank'

    def getLinkURL(self, item):
        """Setup link url."""
        return item.__parent__.absolute_url()

    def rel_path_title(self, rel_path):
        parts = rel_path.split('/')
        context = self.table.context
        for i, part in enumerate(parts):
            current_path = '/'.join(parts[:i + 1])
            parent_path = '/'.join(parts[:i])
            if part == '..':
                current_title = u'..'
                context = context.__parent__
            else:
                context = context[part]
                current_title = context.title
            self.table.paths[current_path] = (parent_path and u'%s/%s' % (self.table.paths[parent_path],
                                              current_title) or current_title)

    def getLinkContent(self, item):
        path = os.path.dirname(item.absolute_url_path())
        rel_path = os.path.relpath(path, self.table.context_path)
        if rel_path not in self.table.paths:
            self.rel_path_title(rel_path)
        return self.table.paths[rel_path]


class EnabledColumn(Column):

    """Column that displays enabled status."""

    header = _("Enabled")
    weight = 30
    cssClasses = {'td': 'enabled-column'}

    def renderCell(self, item):
        if not base_hasattr(item, 'enabled'):
            return u'-'
        if item.enabled:
            icon = ('++resource++collective.documentgenerator/ok.png',
                    translate(_('Enabled'), context=self.request))
        else:
            icon = ('++resource++collective.documentgenerator/nok.png',
                    translate(_('Disabled'), context=self.request))
        return u"<img title='{0}' src='{1}' />".format(
            safe_unicode(icon[1]).replace("'", "&#39;"),
            u"{0}/{1}".format(self.table.portal_url, icon[0]))


class OriginalColumn(Column):

    """Column that displays original status."""

    header = _("Original")
    weight = 40
    cssClasses = {'td': 'original-column'}

    def renderCell(self, item):
        if item.has_been_modified():
            icon = ('++resource++collective.documentgenerator/nok.png',
                    translate(_('Modified'), context=self.request))
        else:
            icon = ('++resource++collective.documentgenerator/ok.png',
                    translate(_('Original'), context=self.request))
        return u"<img title='{0}' src='{1}' />".format(
            safe_unicode(icon[1]).replace("'", "&#39;"),
            u"{0}/{1}".format(self.table.portal_url, icon[0]))


class FormatsColumn(Column):

    """Column that displays pod formats."""

    header = _("Pod formats")
    weight = 50
    cssClasses = {'td': 'formats-column'}

    def renderCell(self, item):
        if not base_hasattr(item, 'pod_formats'):
            return ''
        ret = []
        for fmt in item.pod_formats or []:
            ret.append(u"<img title='{0}' src='{1}' />".format(
                fmt, '%s/++resource++collective.documentgenerator/%s.png' % (self.table.portal_url, fmt)))
        return '\n'.join(ret)


class ReviewStateColumn(Column):

    """Column that displays review state."""

    header = PMF("Review state")
    weight = 60
    cssClasses = {'td': 'state-column'}

    def renderCell(self, item):
        state = api.content.get_state(item)
        if state:
            state_title = self.table.wtool.getTitleForStateOnType(state, item.portal_type)
            return translate(PMF(state_title), context=self.request)
        return ''


class ActionsColumn(Column):
    """
    A column displaying available actions of the listed item.
    Need imio.actionspanel to be used !
    """

    header = _("Actions")
    weight = 70
    params = {'useIcons': True, 'showHistory': False, 'showActions': True, 'showOwnDelete': False,
              'showArrows': True, 'showTransitions': False, 'showExtEdit': True, 'edit_action_class': 'dg_edit_action',
              'edit_action_target': '_blank'}
    cssClasses = {'td': 'actions-column'}

    def renderCell(self, item):
        view = getMultiAdapter((item, self.request), name='actions_panel')
        return view(**self.params)


class DownloadColumn(LinkColumn):

    """Column that displays download action."""

    header = u''
    weight = 80
    cssClasses = {'td': 'download-column'}

    # def renderHeadCell(self):
    #     return u"<img title='{0}' src='{1}' />".format(
    #         translate('Download', domain='plone', context=self.request),
    #         u"{0}/{1}".format(self.table.portal_url, 'download_icon.png'))

    def getLinkURL(self, item):
        """Setup link url."""
        return '%s/@@download' % item.absolute_url()

    def getLinkTitle(self, item):
        """Setup link title."""
        return ' title="%s"' % html.escape(safe_unicode(translate(PMF('Download'), context=self.request)),
                                           quote=True)

    def getLinkContent(self, item):
        down_img = u"<img title='{0}' src='{1}' />".format(
            safe_unicode(translate(PMF('Download'), context=self.request)),
            u"{0}/{1}".format(self.table.portal_url, 'download_icon.png'))
        down_img = u"<img src='{0}' />".format(
            u"{0}/{1}".format(self.table.portal_url, 'download_icon.png'))
        return down_img
