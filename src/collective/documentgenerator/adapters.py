# -*- coding: utf-8 -*-

from collective.documentgenerator.config import VIEWLET_TYPES
from plone import api


class GenerablePODTemplatesAdapter(object):
    """ """
    def __init__(self, context):
        self.context = context

    def get_all_pod_templates(self):
        catalog = api.portal.get_tool(name='portal_catalog')
        brains = catalog.unrestrictedSearchResults(portal_type=VIEWLET_TYPES, sort_on='getObjPositionInParent')
        pod_templates = [self.context.unrestrictedTraverse(brain.getPath()) for brain in brains]

        return pod_templates

    def get_generable_templates(self):
        pod_templates = self.get_all_pod_templates()
        generable_templates = [pt for pt in pod_templates if pt.can_be_generated(self.context)]

        return generable_templates
