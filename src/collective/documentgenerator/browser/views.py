# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from collections import OrderedDict
from collective.documentgenerator.browser.table import TemplatesTable
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.content.pod_template import MailingLoopTemplate
from collective.documentgenerator.content.pod_template import SubTemplate
from collective.documentgenerator.content.style_template import IStyleTemplate
from collective.documentgenerator.utils import translate as _
from OFS.interfaces import IOrderedContainer
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from Products.Five import BrowserView
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope.browserpage import ViewPageTemplateFile
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import alsoProvides
from zope.interface import implementer

import os
import plone


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
                return (level, parent.Title(), ordered.getObjectPosition(obj.getId()))
            return (level, parent.Title(), 0)

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
        # Disable CSRF protection for this request
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request, plone.protect.interfaces.IDisableCSRFProtection)

        self.error = {}
        self.no_obj_found = {}
        self.no_pod_portal_types = {}
        self.not_enabled = {}
        self.not_managed = {}
        self.clean = {}
        self.mailing_loop_templates = {}
        self.sub_templates = {}
        self.left_to_verify = self.find_pod_templates()
        self.check_all_pod_templates()
        self.messages = self.manage_messages
        return self.index()

    def _add_by_path(self, obj, dictionary, context=None, message=None):
        path = "/".join(obj.aq_parent.getPhysicalPath())
        if path not in dictionary:
            dictionary[path] = []
        dictionary[path].append((obj, context, message))

    def excluded_pod_portal_types(self):
        return [
            "StyleTemplate",
        ]

    def check_all_pod_templates(self):
        pod_templates = list(self.left_to_verify)

        for pod_template in pod_templates:

            if not pod_template.enabled:
                self._add_by_path(pod_template, self.not_enabled)
                self.left_to_verify.remove(pod_template)
                continue

            # we do not manage 'StyleTemplate' automatically for now...
            if pod_template.portal_type in self.excluded_pod_portal_types():
                self._add_by_path(pod_template, self.not_managed)
                self.left_to_verify.remove(pod_template)
                continue

            if isinstance(pod_template, MailingLoopTemplate):
                self.mailing_loop_templates[pod_template.UID()] = pod_template
                continue

            if isinstance(pod_template, SubTemplate):
                self.sub_templates[pod_template.UID()] = pod_template
                continue

            if (
                hasattr(pod_template, "pod_portal_types")
                and not pod_template.pod_portal_types
            ):
                self._add_by_path(pod_template, self.no_pod_portal_types)
                self.left_to_verify.remove(pod_template)
                continue

            objs = self.find_context_for(pod_template)
            if not objs:
                self._add_by_path(pod_template, self.no_obj_found)
                self.left_to_verify.remove(pod_template)
                continue

            for obj in objs:
                self.request.set("template_uid", pod_template.UID())
                if hasattr(pod_template, "pod_formats"):
                    output_format = pod_template.pod_formats[0]
                else:
                    output_format = "odt"
                self.request.set("output_format", output_format)

                self.check_pod_template(pod_template, obj, output_format)

                if (
                    hasattr(pod_template, "merge_templates")
                    and pod_template.merge_templates
                ):
                    for merged_template in pod_template.merge_templates:
                        sub_template_uid = merged_template["template"]
                        if sub_template_uid not in self.sub_templates:
                            self.sub_templates[sub_template_uid] = uuidToObject(
                                sub_template_uid
                            )
                        self._add_by_path(
                            self.sub_templates[sub_template_uid], self.clean, obj
                        )
                        if self.sub_templates[sub_template_uid] in self.left_to_verify:
                            self.left_to_verify.remove(
                                self.sub_templates[sub_template_uid]
                            )

                if (
                    hasattr(pod_template, "mailing_loop_template")
                    and pod_template.mailing_loop_template
                ):
                    self.check_mailing_loop(pod_template, obj, output_format)

    def check_pod_template(self, pod_template, obj, output_format):
        try:
            view = obj.restrictedTraverse("@@document-generation")
            view()
            view._generate_doc(
                pod_template, output_format=output_format, raiseOnError=True
            )
            self._add_by_path(pod_template, self.clean, obj)

        except Exception as exc:
            self._add_by_path(pod_template, self.error, obj, (_("Error"), str(exc)))
        self.left_to_verify.remove(pod_template)

    def check_mailing_loop(self, mailed_template, obj, output_format):
        folder = api.content.create(
            type="Folder", title=u"Folder", id="temp_folder", container=self.context
        )

        def do_nothing(ignored_param):
            pass

        mailing_loop_template_uid = mailed_template.mailing_loop_template
        try:
            if mailing_loop_template_uid not in self.mailing_loop_templates.keys():
                mailing_loop_template = uuidToObject(mailing_loop_template_uid)
                self.mailing_loop_templates[
                    mailing_loop_template_uid
                ] = mailing_loop_template
            generation_view = folder.restrictedTraverse(
                "@@persistent-document-generation"
            )
            generation_view.redirects = do_nothing
            generation_view(mailed_template.UID(), "odt")
            persistant_doc = folder.listFolderContents()[0]
            view = folder.restrictedTraverse(
                "@@mailing-loop-persistent-document-generation"
            )
            view.redirects = do_nothing
            view(document_uid=persistant_doc.UID())
            # double check anyway just in case there is an error inside the result file
            view._generate_doc(
                self.mailing_loop_templates[mailing_loop_template_uid],
                output_format=output_format,
                raiseOnError=True,
            )

            self._add_by_path(
                self.mailing_loop_templates[mailing_loop_template_uid], self.clean, obj
            )
        except Exception as exc:
            self._add_by_path(
                self.mailing_loop_templates[mailing_loop_template_uid],
                self.error,
                obj,
                (_("Error"), str(exc)),
            )
        finally:
            api.content.delete(obj=folder)
        self.left_to_verify.remove(
            self.mailing_loop_templates[mailing_loop_template_uid]
        )

    def find_pod_templates(self):
        """
        This will find all potamplates in this site.
        """
        brains = api.content.find(context=self.context,
                                  object_provides=IPODTemplate.__identifier__)
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

        def _search_context(portal_types):
            catalog = api.portal.get_tool("portal_catalog")
            for portal_type in portal_types:
                # get an element for which the TAL condition is True
                brains = catalog(portal_type=portal_type)
                for brain in brains:
                    ctx = brain.getObject()
                    if pod_template.can_be_generated(ctx):
                        return ctx
            return None

        res = []
        if hasattr(pod_template, "pod_portal_types"):
            pod_portal_types = pod_template.pod_portal_types
        else:
            ttool = api.portal.get_tool("portal_types")
            pod_portal_types = ttool.listContentTypes()
        found_context = _search_context(pod_portal_types)
        if found_context:
            res.append(found_context)
        return res

    @property
    def manage_messages(self):
        messages = OrderedDict()
        for left_over in self.left_to_verify:
            self._add_by_path(
                left_over, self.error, None, (_("Error"), _("Could not check"))
            )
        messages["check_pod_template_error"] = self.error
        messages["check_pod_template_no_obj_found"] = self.no_obj_found
        messages["check_pod_template_no_pod_portal_types"] = self.no_pod_portal_types
        messages["check_pod_template_not_enabled"] = self.not_enabled
        messages["check_pod_template_not_managed"] = self.not_managed
        messages["check_pod_template_clean"] = self.clean
        return messages
