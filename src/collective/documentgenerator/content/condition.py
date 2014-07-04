# -*- coding: utf-8 -*-

from collective.documentgenerator.interfaces import IPODTemplateCondition

from zope.interface import implements


class PODTemplateCondition(object):
    """
    """
    implements(IPODTemplateCondition)

    def __init__(self, pod_template, context):
        self.pod_template = pod_template
        self.context = context

    def evaluate(self):
        return True
