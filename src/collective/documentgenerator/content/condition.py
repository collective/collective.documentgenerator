# -*- coding: utf-8 -*-

from collective.behavior.talcondition.behavior import ITALCondition

from collective.documentgenerator.interfaces import IPODTemplateCondition

from zope.interface import implements


class PODTemplateCondition(object):
    """ """

    implements(IPODTemplateCondition)

    def __init__(self, pod_template, context):
        self.pod_template = pod_template
        self.context = context

    def evaluate(self):
        enabled = self.pod_template.enabled
        return enabled


class SubTemplateCondition(PODTemplateCondition):
    """ """

    def evaluate(self):
        """
        By default, subtemplates are not supposed to be rendered by users.
        """
        return False


class ConfigurablePODTemplateCondition(PODTemplateCondition):
    """
    Check the permission and the  TAL expression of a PODTemplate
    on a context.
    """

    def evaluate(self):
        """
        Check if :
        - template is enabled;
        - template is restricted to specific portal_types;
        - the tal_condition is True.
        """
        return self.pod_template.enabled and \
            self.evaluate_allowed_context(self.context) and \
            ITALCondition(self.pod_template).evaluate(extra_expr_ctx={'here': self.context,
                                                                      'context': self.context,
                                                                      'template': self.pod_template})

    def evaluate_allowed_context(self, context):
        """
        Evaluate if context is in pt selected list
        If not use, return True
        """
        allowed_types = self.pod_template.pod_portal_types
        return not allowed_types or context.portal_type in allowed_types
