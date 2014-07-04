# -*- coding: utf-8 -*-

from plone import api

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class PermissionsVocabularyFactory(object):
    """
    Vocabulary factory for pod_permission field.
    """

    def __call__(self, context):
        control_panel = api.portal.get_tool('portal_controlpanel')
        all_permissions = control_panel.possible_permissions()
        vocabulary = SimpleVocabulary([SimpleTerm(p, p, p) for p in all_permissions])
        return vocabulary
