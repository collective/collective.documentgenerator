# -*- coding: utf-8 -*-

from plone import api

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class PortalTypeVocabularyFactory(object):
    """
    Vocabulary factory for pod_type field.
    """

    def __call__(self, context):
        control_panel = api.portal.get_tool('portal_types')
        all_pt = control_panel.listContentTypes()
        vocabulary = SimpleVocabulary([SimpleTerm(p, p, p) for p in all_pt])
        return vocabulary
