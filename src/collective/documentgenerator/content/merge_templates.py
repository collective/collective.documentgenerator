# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import ITemplatesToMerge
from zope.interface import implementer


@implementer(ITemplatesToMerge)
class TemplatesToMergeForPODTemplate(object):
    """
    """
    def __init__(self, pod_template):
        self.pod_template = pod_template

    def get(self):
        return {}
