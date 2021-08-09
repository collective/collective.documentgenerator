# -*- coding: utf-8 -*-

from collective.documentgenerator import _
from collective.documentgenerator.config import get_column_modifier
from collective.documentgenerator.config import get_csv_field_delimiters
from collective.documentgenerator.config import get_csv_string_delimiters
from collective.documentgenerator.config import POD_FORMATS
from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.utils import get_site_root_relative_path
from plone import api
from Products.CMFPlone.utils import safe_unicode
from z3c.form.i18n import MessageFactory as _z3c_form
from z3c.form.interfaces import IContextAware
from z3c.form.interfaces import IDataManager
from z3c.form.term import MissingChoiceTermsVocabulary
from z3c.form.term import MissingTermsMixin
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
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

    def _portal_types(self):
        return ['PODTemplate', 'SubTemplate']

    def _render_term_title(self, brain):
        return brain.Title

    def __call__(self, context):
        catalog = api.portal.get_tool('portal_catalog')
        pod_templates = catalog(
            portal_type=self._portal_types(),
            sort_on='sortable_title',
            sort_order='ascending',
        )
        voc_terms = [SimpleTerm('--NOVALUE--', '--NOVALUE--', _z3c_form('No value'))]

        for brain in pod_templates:
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, self._render_term_title(brain)))

        vocabulary = SimpleVocabulary(voc_terms)

        return vocabulary


class ConfigColumnModifierVocabularyFactory(object):
    """
    Vocabulary factory for control panel 'column_modifier' field.
    """

    def __call__(self, context):
        voc_terms = [
            SimpleTerm('disabled', 0, _('Disabled')),
            SimpleTerm('nothing', 1, _('Nothing')),
            SimpleTerm('optimize', 2, _('Optimize')),
            SimpleTerm('distribute', 3, _('Distribute'))]

        return SimpleVocabulary(voc_terms)


class PodColumnModifierVocabularyFactory(object):
    """
    Vocabulary factory for pod template 'column_modifier' field.
    """

    def __call__(self, context):
        # adapt first term value depending on global configuration value
        # get term from global value vocabulary
        vocabulary = queryUtility(
            IVocabularyFactory, 'collective.documentgenerator.ConfigColumnModifier')
        voc = vocabulary(context)
        global_value = _(voc.getTerm(get_column_modifier()).title)
        global_value_term = _('Global value (${global_value})',
                              mapping={'global_value': global_value})

        voc_terms = [
            SimpleTerm(-1, -1, global_value_term),
            SimpleTerm('disabled', 0, _('Force disabled')),
            SimpleTerm('nothing', 1, _('Force nothing')),
            SimpleTerm('optimize', 2, _('Force optimize')),
            SimpleTerm('distribute', 3, _('Force distribute'))]

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


class ExistingPODTemplateFactory(object):
    """
    Vocabulary factory with all existing_pod_templates.
    """

    def __call__(self, context):
        voc_terms = []

        for brain in self._get_existing_pod_templates(context, enabled_only=False):
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, self._renderTermTitle(brain)))

        return SimpleVocabulary(voc_terms)

    def _get_existing_pod_templates(self, context, enabled_only=False):
        brains = []
        catalog = api.portal.get_tool('portal_catalog')
        for brain in catalog(object_provides=IConfigurablePODTemplate.__identifier__):
            template = brain.getObject()
            if enabled_only and not template.enabled:
                continue
            if template.is_reusable and template != context:
                brains.append(brain)
        return brains

    def _renderTermTitle(self, brain):
        return u'{} -> {}'.format(safe_unicode(brain.Title), safe_unicode(brain.getObject().odt_file.filename))


class AllPODTemplateWithFileVocabularyFactory(object):
    """
    Vocabulary factory with all existing pod_templates.
    """

    def __call__(self, context):
        voc_terms = [SimpleTerm('all', 'all', _('All POD templates'))]

        for brain in self._get_all_pod_templates_with_file():
            voc_terms.append(SimpleTerm(brain.UID, brain.UID, self._renderTermTitle(brain)))

        return SimpleVocabulary(voc_terms)

    def _get_all_pod_templates_with_file(self):
        brains = []
        catalog = api.portal.get_tool('portal_catalog')
        for brain in catalog(object_provides=IPODTemplate.__identifier__):
            template = brain.getObject()
            if hasattr(template, "odt_file") and template.odt_file:
                brains.append(brain)
        return brains

    def _renderTermTitle(self, brain):
        return u'{} ({})'.format(
            safe_unicode(get_site_root_relative_path(brain.getObject())),
            safe_unicode(brain.Title))


class CSVFieldDelimiterFactory(object):
    def __call__(self, context):
        voc_terms = []
        for title, delimiter in get_csv_field_delimiters().items():
            voc_terms.append(SimpleTerm(delimiter, title, _(title)))

        return SimpleVocabulary(voc_terms)


class CSVStringDelimiterFactory(object):
    def __call__(self, context):
        voc_terms = []
        for title, delimiter in get_csv_string_delimiters().items():
            voc_terms.append(SimpleTerm(delimiter, title, _(title)))

        return SimpleVocabulary(voc_terms)

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


class ConfigStreamVocabularyFactory(object):
    """
    Vocabulary factory for control panel 'use_stream' field.
    """

    def __call__(self, context):
        voc_terms = [
            SimpleTerm(u'auto', u'auto', _('Auto')),
            SimpleTerm(True, True, _('Yes')),
            SimpleTerm(False, False, _('No')),
        ]

        return SimpleVocabulary(voc_terms)
