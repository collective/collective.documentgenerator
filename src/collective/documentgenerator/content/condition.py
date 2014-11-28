# -*- coding: utf-8 -*-

from collective.behavior.talcondition.behavior import ITALCondition

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


class ConfigurablePODTemplateCondition(PODTemplateCondition):
    """
    Check the permission and the  TAL expression of a PODTemplate
    on a context.
    """

    def evaluate(self):
        allowed_context = self.evaluate_allowed_context(self.context)
        tal_condition = ITALCondition(self.pod_template)
        evaluated_tal_condition = tal_condition.evaluate()
        enabled = self.pod_template.enabled

        return enabled and allowed_context and evaluated_tal_condition

    def evaluate_allowed_context(self, context):
        """
        Evaluate if context is in pt selected list
        If not use, return True
        """
        allowed_types = self.pod_template.pod_portal_type

        if not allowed_types:
            return True

        allowed_context = context.portal_type in allowed_types

        return allowed_context
