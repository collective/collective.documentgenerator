# -*- coding: utf-8 -*-
"""Helper view for dexterity content types."""

from ..interfaces import IFieldRendererForDocument
from .base import DisplayProxyObject
from .base import DocumentGenerationHelperView
from bs4 import BeautifulSoup as Soup
from collective.excelexport.exportables.dexterityfields import get_ordered_fields
from plone import api
from plone.app.textfield import RichTextValue
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.behavior.interfaces import IBehavior
from plone.rfc822.interfaces import IPrimaryFieldInfo
from plone.supermodel.utils import mergedTaggedValueDict
from z3c.form.interfaces import NO_VALUE
from zope.component import getMultiAdapter
from zope.component import getUtility


class DXDocumentGenerationHelperView(DocumentGenerationHelperView):

    """Helper view for dexterity content types."""

    def __init__(self, context, request):
        super(DXDocumentGenerationHelperView, self).__init__(context, request)
        self.fti = api.portal.get_tool('portal_types')[context.portal_type]
        # reverse fields order so that the content schema have priority on the behaviors fields
        self.fields = dict(reversed(get_ordered_fields(self.fti)))

    def has_field(self, field_name):
        """ Check if fieldname is a field. Useful when behavior is optional """
        return field_name in self.fields

    def get_field(self, field_name):
        """Get field."""
        return self.fields.get(field_name)

    def get_field_schema(self, field_name):
        """Get schema for given field."""
        schema = self.fti.lookupSchema()
        if field_name in schema:
            return schema
        else:
            for behavior_id in self.fti.behaviors:
                schema = getUtility(IBehavior, behavior_id).interface
                if field_name in schema:
                    return schema

        return None

    def get_field_renderer(self, field_name):
        """Get the dexterity field renderer for this field."""
        field = self.get_field(field_name)
        renderer = getMultiAdapter(
            (field, self.real_context, self.request), IFieldRendererForDocument)
        return renderer

    def display(self, field_name, no_value='', bypass_check_permission=False):
        """Display field value."""
        if bypass_check_permission or self.check_permission(field_name):
            field_renderer = self.get_field_renderer(field_name)
            display_value = field_renderer.render_value()
            if not display_value:
                display_value = no_value
        else:
            display_value = u''

        return display_value

    def check_permission(self, field_name):
        """Check field permission."""
        schema = self.get_field_schema(field_name)
        read_permissions = mergedTaggedValueDict(
            schema, READ_PERMISSIONS_KEY)
        permission = read_permissions.get(field_name)
        if permission is None:
            return True

        user = api.user.get_current()
        return api.user.has_permission(permission, user=user, obj=self.real_context)

    def get_value(self, field_name, default=None, as_utf8=False, strict=True):
        """
            strict: if False and field doesn't exist, be cool and return default value
        """
        if not strict and not self.has_field(field_name):
            return default
        value = getattr(self.real_context, field_name)
        if value is None:
            return default
        if isinstance(value, NO_VALUE.__class__):
            return default
        if isinstance(value, RichTextValue):
            value = value.output
        if as_utf8 and isinstance(value, unicode):
            value = value.encode('utf8')
        return value

    def display_voc(self, field_name, separator=', '):
        field_renderer = self.get_field_renderer(field_name)
        field_renderer.exportable.separator = separator
        return field_renderer.render_value()

    def display_widget(self, field_name, clean=True, soup=False):
        obj_view = getMultiAdapter((self.real_context, self.request), name=u'view')
        obj_view.updateFieldsFromSchemata()
        for field in obj_view.fields:
            if field != field_name:
                obj_view.fields = obj_view.fields.omit(field)
        obj_view.updateWidgets()
        widget = obj_view.widgets[field_name]
        rendered = widget.render()  # unicode
        if clean or soup:
            souped = Soup(rendered, "html.parser")
            if clean:
                for tag in souped.find_all(class_='required'):
                    tag.extract()
                for tag in souped.find_all(type='hidden'):
                    tag.extract()
            if soup:
                return souped
            else:
                return str(souped)  # is utf8
        else:
            return rendered.encode('utf8')

    def get_file_binary(self, file_obj):
        """ """
        primary_field_infos = IPrimaryFieldInfo(file_obj)
        return primary_field_infos.value.data


class DXDisplayProxyObject(DisplayProxyObject):

    """Dexterity implementation of DisplayProxyObject."""

    def is_field(self, attr_name):
        ttool = api.portal.get_tool('portal_types')
        fti = ttool[self.context.portal_type]
        is_field = bool(fti.lookupSchema().get(attr_name))
        if not is_field:
            # check if it is a behavior field
            for behavior_id in fti.behaviors:
                schema = getUtility(IBehavior, behavior_id).interface
                if not IFormFieldProvider.providedBy(schema):
                    continue

                is_field = bool(schema.get(attr_name))

        return is_field
