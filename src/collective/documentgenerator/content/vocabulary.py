# -*- coding: utf-8 -*-

from plone import api

from z3c.form.i18n import MessageFactory as _

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class PortalTypeVocabularyFactory(object):
    """
    Vocabulary factory for pod_type field.
    """

    def __call__(self, context):
        control_panel = api.portal.get_tool('portal_types')
        all_portaltypes = control_panel.listContentTypes()
        vocabulary = SimpleVocabulary([SimpleTerm(p, p, p) for p in all_portaltypes])
        return vocabulary


class StyleVocabularyFactory(object):
    """
    Vocabulary factory for style field.
    """

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        style_template_brains = catalog(portal_type='StyleTemplate')
        voc_terms = [SimpleTerm('--NOVALUE--', '--NOVALUE--', _('No value'))]

        for brain in style_template_brains:
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, brain.Title))

        vocabulary = SimpleVocabulary(voc_terms)

        return vocabulary


class MergeTemplatesVocabularyFactory(object):
    """
    Vocabulary factory for merge_templates field.
    """

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        pod_templates = catalog(
            portal_type=['PODTemplate', 'SubTemplate'],
            sort_on='sortable_title',
            sort_order='ascending',
        )
        voc_terms = [SimpleTerm('--NOVALUE--', '--NOVALUE--', _('No value'))]

        for brain in pod_templates:
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, brain.Title))

        vocabulary = SimpleVocabulary(voc_terms)

        return vocabulary
