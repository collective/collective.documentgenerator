# -*- coding: utf-8 -*-

from plone import api

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class PermissionsVocabularyFactory(object):
    """
    Vocabulary factory for localities.
    """

    def __call__(self, context):
        control_panel = api.portal.get_tool('portal_controlpanel')

        vocabulary_terms = []
        for permission in control_panel.possible_permissions():
            vocabulary_terms.append(
                SimpleTerm(permission, permission, permission)
            )

        vocabulary = SimpleVocabulary(vocabulary_terms)
        return vocabulary
