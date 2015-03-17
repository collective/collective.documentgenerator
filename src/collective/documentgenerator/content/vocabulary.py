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
        all_pt = control_panel.listContentTypes()
        vocabulary = SimpleVocabulary([SimpleTerm(p, p, p) for p in all_pt])
        return vocabulary


class StyleVocabularyFactory(object):
    """
    Vocabulary factory for style field.
    """

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        style_template_brains = catalog(portal_type='StyleTemplate')
        style_templates = [SimpleTerm('--NOVALUE--', '--NOVALUE--', _('No value'))]

        for brain in style_template_brains:
            style_templates.append(SimpleTerm(brain.UID, brain.UID, brain.Title))

        vocabulary = SimpleVocabulary(style_templates)

        return vocabulary
