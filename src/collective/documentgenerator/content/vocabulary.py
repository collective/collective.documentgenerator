# -*- coding: utf-8 -*-

from collective.documentgenerator import _
from collective.documentgenerator.config import POD_FORMATS
from collective.documentgenerator.config import get_optimize_tables

from plone import api

from z3c.form.i18n import MessageFactory as _z3c_form
from z3c.form.interfaces import IContextAware, IDataManager
from z3c.form.term import MissingChoiceTermsVocabulary, MissingTermsMixin

from zope.component import getMultiAdapter, getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class FormatsVocabularyFactory(object):
    """
    Vocabulary factory for 'pod_formats' field.
    """

    def __call__(self, context):
        vocabulary = SimpleVocabulary([SimpleTerm(pod_format, pod_format, label) for pod_format, label in POD_FORMATS])
        return vocabulary


class PortalTypesVocabularyFactory(object):
    """
    Vocabulary factory for 'pod_portal_types' field.
    """

    def __call__(self, context):
        control_panel = api.portal.get_tool('portal_types')
        all_portaltypes = control_panel.listContentTypes()
        vocabulary = SimpleVocabulary([SimpleTerm(p, p, p) for p in all_portaltypes])
        return vocabulary


class StyleTemplatesVocabularyFactory(object):
    """
    Vocabulary factory for 'style_template' field.
    """

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        style_template_brains = catalog(portal_type='StyleTemplate')
        voc_terms = [SimpleTerm('--NOVALUE--', '--NOVALUE--', _z3c_form('No value'))]

        for brain in style_template_brains:
            voc_terms.append(SimpleTerm(brain.UID,
                                        brain.UID,
                                        self._renderTermTitle(brain)))

        vocabulary = SimpleVocabulary(voc_terms)

        return vocabulary

    def _renderTermTitle(self, brain):
        return brain.Title


class MergeTemplatesVocabularyFactory(object):
    """
    Vocabulary factory for 'merge_templates' field.
    """

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        pod_templates = catalog(
            portal_type=['PODTemplate', 'SubTemplate'],
            sort_on='sortable_title',
            sort_order='ascending',
        )
        voc_terms = [SimpleTerm('--NOVALUE--', '--NOVALUE--', _z3c_form('No value'))]

        for brain in pod_templates:
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, brain.Title))

        vocabulary = SimpleVocabulary(voc_terms)

        return vocabulary


class OptimizeTablesVocabularyFactory(object):
    """
    Vocabulary factory for 'optimize_tables' field.
    """

    def __call__(self, context):
        # adapt first term value depending on global configuration value
        global_value = _('Global value (disabled)')
        if get_optimize_tables():
            global_value = _('Global value (enabled)')

        voc_terms = [
            SimpleTerm(-1, -1, global_value),
            SimpleTerm(0, 0, _('Force disable')),
            SimpleTerm(1, 1, _('Force enable'))]

        return SimpleVocabulary(voc_terms)


def get_mailing_loop_templates(enabled_only=True):
    brains = []
    catalog = api.portal.get_tool('portal_catalog')

    for brain in catalog(portal_type='MailingLoopTemplate'):
        if enabled_only and not brain.getObject().enabled:
            continue
        brains.append(brain)
    return brains


class MailingLoopTemplatesEnabledVocabularyFactory(object):
    """
    Vocabulary factory for 'mailing_loop_template' field.
    """

    def __call__(self, context):
        voc_terms = []

        for brain in get_mailing_loop_templates(enabled_only=True):
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, self._renderTermTitle(brain)))
        return SimpleVocabulary(voc_terms)

    def _renderTermTitle(self, brain):
        return brain.Title


class MailingLoopTemplatesAllVocabularyFactory(object):
    """
    Vocabulary factory with all mailing_loop_template.
    """

    def __call__(self, context):
        voc_terms = []

        for brain in get_mailing_loop_templates(enabled_only=False):
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, self._renderTermTitle(brain)))

        return SimpleVocabulary(voc_terms)

    def _renderTermTitle(self, brain):
        return brain.Title


#########################
# vocabularies adapters #
#########################


class MissingTerms(MissingTermsMixin):

    def getTerm(self, value):
        try:
            return super(MissingTermsMixin, self).getTerm(value)
        except LookupError:
            try:
                return self.complete_voc().getTerm(value)
            except LookupError:
                pass
        if (IContextAware.providedBy(self.widget) and not self.widget.ignoreContext):
            curValue = getMultiAdapter((self.widget.context, self.field), IDataManager).query()
            if curValue == value:
                return self._makeMissingTerm(value)
        raise

    def getTermByToken(self, token):
        try:
            return super(MissingTermsMixin, self).getTermByToken(token)
        except LookupError:
            try:
                return self.complete_voc().getTermByToken(token)
            except LookupError:
                pass
        if (IContextAware.providedBy(self.widget) and not self.widget.ignoreContext):
            value = getMultiAdapter((self.widget.context, self.field), IDataManager).query()
            term = self._makeMissingTerm(value)
            if term.token == token:
                return term
        raise LookupError(token)


class PTMCTV(MissingChoiceTermsVocabulary, MissingTerms):
    """ Managing missing terms for IImioDmsIncomingMail. """

    def complete_voc(self):
        if self.field.getName() == 'mailing_loop_template':
            return getUtility(IVocabularyFactory, 'collective.documentgenerator.AllMailingLoopTemplates')(self.context)
        else:
            return SimpleVocabulary([])
