# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface

from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICollectiveDocumentgeneratorLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class PODTemplateNotFoundError(Exception):
    """ """


class IPODTemplateCondition(Interface):
    """Condition object adapting a pod_template and a context."""

    def evaluate(self):
        """Represent the condition evaluation by returning True or False."""
