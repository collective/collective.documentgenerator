# -*- coding: utf-8 -*-

from DateTime import DateTime
from zope.event import notify

from Products.Archetypes.interfaces.base import IBaseFolder

from collective.documentgenerator.config import HAS_PLONE_5
from collective.documentgenerator.helper import ATDocumentGenerationHelperView
from collective.documentgenerator.helper import DocumentGenerationHelperView
from collective.documentgenerator.helper import DXDocumentGenerationHelperView
from collective.documentgenerator.utils import translate as _

from plone import api
from plone.dexterity.events import EditCancelledEvent
from plone.app.textfield import RichText
from plone.dexterity.interfaces import IDexterityContainer

from zope.component import getUtility
from zope.schema import List
from zope.i18n.interfaces import ITranslationDomain


class BaseDemoHelperView(DocumentGenerationHelperView):
    """ """

    def get_default_CT_fields(self):
        raise NotImplementedError

    def _get_default_CT_fields_filtered_fields(self):
        """ """
        return ['id', 'title']

    def is_default_field(self, field_name):
        if not self.is_rich_text_field(field_name) and not self.is_line_field(field_name):
            return True
        return False

    def is_rich_text_field(self, field_name):
        raise NotImplementedError

    def is_line_field(self, field_name):
        raise NotImplementedError

    def get_localized_field_name(self, field_name):
        translation_domain = getUtility(ITranslationDomain, 'plone')
        if not HAS_PLONE_5:
            properties = api.portal.get_tool('portal_properties')
            target_language = properties.site_properties.default_language
        else:
            target_language = api.portal.get_registry_record('plone.default_language')

        unlocalized_field_label = self._get_unlocalized_field_label(field_name)

        translation = translation_domain.translate(
            unlocalized_field_label,
            target_language=target_language,
            default=field_name
        )
        return translation

    def _get_unlocalized_field_label(self, field_name):
        raise NotImplementedError

    def get_slash_separated_date(self, date):
        date = DateTime(date)
        formatted_date = date.strftime('%d/%m/%Y %H:%M')
        return formatted_date

    def display_code(self, field_name):
        code = []
        if self.is_default_field(field_name):
            code.append('%s : context.%s' % (_(u'input_field'), field_name))
        elif self.is_rich_text_field(field_name):
            code.append("%s : do text from view.render_xhtml('%s')" % (_(u'comment'), field_name))
        elif self.is_line_field(field_name):
            code.append('%s : line' % _(u'input_field'))
            code.append("%s : do text for line in view.list('%s')" % (_(u'comment'), field_name))
        return code

    def summary(self, obj):
        summary = '%s - %s - %s %s' % \
            (obj.Title(), obj.creators[0], _(u'last_change'), obj.modification_date.strftime('%d/%m/%Y %H:%M'))
        return summary

    def get_collection_CT_fields(self):
        raise NotImplementedError

    def _get_collection_CT_fields_filtered_fields(self):
        """ """
        return ['id', 'title', 'text', 'sort_on', 'sort_reversed', 'b_size', 'limit', 'customViewFields']

    def is_folderish(self):
        raise NotImplementedError


class ATDemoHelperView(ATDocumentGenerationHelperView, BaseDemoHelperView):
    """
    Archetypes implementation of demo document generation helper methods.
    """

    def get_default_CT_fields(self):
        field_list = []
        filtered_fields = self._get_default_CT_fields_filtered_fields()
        default_field_list = self.real_context.schema.getSchemataFields('default')
        for field in default_field_list:
            if field.getName() not in filtered_fields:
                field_list.append(field.getName())
        return field_list

    def is_rich_text_field(self, field_name):
        return self.real_context.schema.get(field_name).getWidgetName() == 'RichWidget'

    def is_line_field(self, field_name):
        return self.real_context.schema.get(field_name).getWidgetName() == 'LinesWidget'

    def _get_unlocalized_field_label(self, field_name):
        return self.real_context.getField(field_name).widget.Label(self)

    def is_folderish(self):
        return IBaseFolder.providedBy(self.real_context)

    def get_collection_CT_fields(self):
        field_list = []
        filtered_fields = self._get_collection_CT_fields_filtered_fields()
        default_field_list = self.real_context.schema.getSchemataFields('default')
        for field in default_field_list:
            if field.getName() not in filtered_fields:
                field_list.append(field.getName())
        return field_list


class DXDemoHelperView(DXDocumentGenerationHelperView, BaseDemoHelperView):
    """
    Dexterity implementation of demo document generation helper methods.
    """

    def get_default_CT_fields(self):
        field_list = []
        filtered_fields = self._get_default_CT_fields_filtered_fields()
        default_field_list = self._get_fields()
        for field in default_field_list:
            if field.__name__ not in filtered_fields:
                field_list.append(field.__name__)
        return field_list

    def _get_fields(self, fieldsets=['default']):
        with api.env.adopt_roles(['Manager']):
            edit_form = self.real_context.unrestrictedTraverse('@@edit').form_instance
            edit_form.update()
            notify(EditCancelledEvent(self.real_context))

        fields = edit_form.fields.values()
        return [f.field for f in fields]

    def _get_field(self, field_name):
        fields = self._get_fields()
        for field in fields:
            if field.__name__ == field_name:
                return field

    def is_rich_text_field(self, field_name):
        field = self._get_field(field_name)
        if field and isinstance(field, RichText):
            return True
        return False

    def is_line_field(self, field_name):
        field = self._get_field(field_name)
        if field and isinstance(field, List):
            return True
        return False

    def _get_unlocalized_field_label(self, field_name):
        field = self._get_field(field_name)
        return field.title

    def get_collection_CT_fields(self):
        field_list = []
        filtered_fields = self._get_collection_CT_fields_filtered_fields()
        default_field_list = self._get_fields()
        for field_name, field in default_field_list:
            if field_name not in filtered_fields:
                field_list.append(field_name)
        return field_list

    def is_folderish(self):
        return IDexterityContainer.providedBy(self.real_context)
