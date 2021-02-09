# -*- coding: utf-8 -*-
from collections import OrderedDict

from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from collective.documentgenerator.browser.table import TemplatesTable
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.content.style_template import IStyleTemplate
from collective.documentgenerator.utils import translate as _
from OFS.interfaces import IOrderedContainer
from plone import api
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from Products.Five import BrowserView
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope.browserpage import ViewPageTemplateFile
from zope.component.hooks import getSite
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import implementer

import os


class ResetMd5(BrowserView):
    def __call__(self):
        self.context.style_modification_md5 = self.context.current_md5


class TemplatesListing(BrowserView):

    __table__ = TemplatesTable
    provides = [IPODTemplate.__identifier__, IStyleTemplate.__identifier__]
    depth = None
    local_search = True

    def __init__(self, context, request):
        super(TemplatesListing, self).__init__(context, request)

    def query_dict(self):
        crit = {"object_provides": self.provides}
        if self.local_search:
            container_path = "/".join(self.context.getPhysicalPath())
            crit["path"] = {"query": container_path}
            if self.depth is not None:
                crit["path"]["depth"] = self.depth
        # crit['sort_on'] = ['path', 'getObjPositionInParent']
        # how to sort by parent path
        # crit['sort_on'] = 'path'
        return crit

    def update(self):
        self.table = self.__table__(self.context, self.request)
        self.table.__name__ = u"dg-templates-listing"
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog.searchResults(**self.query_dict())
        res = [
            (brain.getObject(), os.path.dirname(brain.getPath())) for brain in brains
        ]

        def keys(param):
            """ Goal: order by level of folder, parent folder, position in folder,"""
            (obj, path) = param
            level = len(path.split("/"))
            parent = aq_parent(aq_inner(obj))
            ordered = IOrderedContainer(parent, None)
            if ordered is not None:
                return (level, path, ordered.getObjectPosition(obj.getId()))
            return (level, path, 0)

        # sort by parent path and by position
        self.table.results = [tup[0] for tup in sorted(res, key=keys)]
        self.table.update()

    def __call__(self, local_search=None, search_depth=None):
        """
            search_depth = int value (0)
            local_search = bool value
        """
        if search_depth is not None:
            self.depth = search_depth
        else:
            sd = self.request.get("search_depth", "")
            if sd:
                self.depth = int(sd)
        if local_search is not None:
            self.local_search = local_search
        else:
            self.local_search = "local_search" in self.request or self.local_search
        self.update()
        return self.index()


class DisplayChildrenPodTemplateProvider(ContentProviderBase):
    template = ViewPageTemplateFile("children_pod_template.pt")

    @property
    def name(self):
        """ """
        return self.__name__

    @property
    def value(self):
        """ """
        return self.render()

    @property
    def label(self):
        return ""

    def get_children(self):
        return self.context.get_children_pod_template()

    def render_child(self, child):
        return "{0} ({1})".format(child.Title(), child.absolute_url())

    def render(self):
        return self.template()


@implementer(IFieldsAndContentProvidersForm)
class ViewConfigurablePodTemplate(DefaultView):
    contentProviders = ContentProviders()

    contentProviders["children_pod_template"] = DisplayChildrenPodTemplateProvider
    contentProviders["children_pod_template"].position = 4


@implementer(IFieldsAndContentProvidersForm)
class EditConfigurablePodTemplate(DefaultEditForm):
    contentProviders = ContentProviders()

    contentProviders["children_pod_template"] = DisplayChildrenPodTemplateProvider
    contentProviders["children_pod_template"].position = 4


class CheckPodTemplatesView(BrowserView):
    """
      Check existing pod templates to try to find one out that is generating errors.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        '''Generate Pod Templates and check if some are genering errors.'''
        self.messages = self.manage_messages()
        return self.index()

    def manage_messages(self):
        ''' '''
        error = []
        no_obj_found = []
        no_pod_portal_types = []
        not_enabled = []
        not_managed = []
        clean = []

        pod_templates = self.find_pod_templates()
        for pod_template in pod_templates:

            if not pod_template.enabled:
                not_enabled.append((pod_template, None))
                continue

            # we do not manage 'StyleTemplate' automatically for now...
            if pod_template.portal_type in ('StyleTemplate', 'DashboardPODTemplate',
                                            'SubTemplate', 'MailingLoopTemplate'):
                not_managed.append((pod_template, None))
                continue

            # here we have a 'ConfigurablePODTemplate'
            if hasattr(pod_template, 'pod_portal_types') and not pod_template.pod_portal_types:
                no_pod_portal_types.append((pod_template, None))
                continue

            objs = self.find_context_for(pod_template)
            if not objs:
                no_obj_found.append((pod_template, None))
                continue

            for obj in objs:
                self.request.set('template_uid', pod_template.UID())
                view = obj.restrictedTraverse('@@document-generation')
                if hasattr(pod_template, "pod_formats"):
                    output_format = pod_template.pod_formats[0]
                else:
                    output_format = 'odt'
                self.request.set('output_format', output_format)
                try:
                    view()
                    view._generate_doc(pod_template, output_format=output_format, raiseOnError=True)
                    clean.append((pod_template, obj))
                except Exception as exc:
                    error.append((pod_template, obj, (_('Error'), exc.message)))

        messages = OrderedDict()
        messages[_('check_pod_template_error')] = error
        messages[_('check_pod_template_no_obj_found')] = no_obj_found
        messages[_('check_pod_template_no_pod_portal_types')] = no_pod_portal_types
        messages[_('check_pod_template_not_enabled')] = not_enabled
        messages[_('check_pod_template_not_managed')] = not_managed
        messages[_('check_pod_template_clean')] = clean
        return messages

    def find_pod_templates(self):
        """
        This will find all potamplates in this site.
        """
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(object_provides=IPODTemplate.__identifier__)
        res = []
        for brain in brains:
            pod_template = brain.getObject()
            res.append(pod_template)
        return res

    def find_context_for(self, pod_template):
        """
        This will find context objects working with given p_pod_template.
        We return one obj of each pod_portal_types respecting the TAL condition.
        """
        catalog = api.portal.get_tool('portal_catalog')
        res = []
        if hasattr(pod_template, "pod_portal_types"):
            pod_portal_types = pod_template.pod_portal_types
        else:
            site = getSite()
            ttool = getToolByName(site, 'portal_types', None)
            if ttool is None:
                res = []
            pod_portal_types = ttool.listContentTypes()

        for pod_portal_type in pod_portal_types:
            # get an element for which the TAL condition is True
            brains = catalog(portal_type=pod_portal_type)
            for brain in brains:
                obj = brain.getObject()
                if pod_template.can_be_generated(obj):
                    res.append(obj)
                    break
        return res
