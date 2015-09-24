# -*- coding: utf-8 -*-
"""Helper view for dexterity content types."""
from zope.component import getMultiAdapter
from zope.component import getUtility

from plone import api
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.supermodel.utils import mergedTaggedValueDict

from collective.excelexport.exportables.dexterityfields import get_ordered_fields

from collective.documentgenerator.helper import DocumentGenerationHelperView
from collective.documentgenerator.helper import DisplayProxyObject
from collective.documentgenerator.interfaces import IFieldRendererForDocument


class DXDocumentGenerationHelperView(DocumentGenerationHelperView):

    """Helper view for dexterity content types."""

    def __init__(self, context, request):
        super(DXDocumentGenerationHelperView, self).__init__(context, request)
        self.fti = api.portal.get_tool('portal_types')[context.portal_type]
        # reverse fields order so that the content schema have priority on the behaviors fields
        self.fields = dict(reversed(get_ordered_fields(self.fti)))

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

    def display(self, field_name, context=None, no_value=''):
        """Display field value."""
        if context is None:
            context = self.real_context

        if self.check_permission(field_name, context):
            field_renderer = self.get_field_renderer(field_name, context)
            display_value = field_renderer.render_value()
            if not display_value:
                display_value = no_value
        else:
            display_value = u''

        return display_value

    def check_permission(self, field_name, context):
        """Check field permission."""
        schema = self.get_field_schema(field_name)
        read_permissions = mergedTaggedValueDict(
            schema, READ_PERMISSIONS_KEY)
        permission = read_permissions.get(field_name)
        if permission is None:
            return True

        user = api.user.get_current()
        return api.user.has_permission(permission, user=user, obj=context)

    def get_field_renderer(self, field_name, context):
        """Get the dexterity field renderer for this field."""
        field = self.get_field(field_name)
        renderer = getMultiAdapter(
            (field, context, self.request), IFieldRendererForDocument)

        return renderer

    def get_value(self, field_name):
        return getattr(self.real_context, field_name)

    def display_date(self, field_name, context=None, long_format=None, time_only=None, custom_format=None):
        date = self.get_value(field_name)
        if not custom_format:
            # use toLocalizedTime
            formatted_date = self.plone.toLocalizedTime(date, long_format, time_only)
        else:
            formatted_date = date.strftime(custom_format)

        return formatted_date

    def display_voc(self, field_name, context=None, separator=', '):
        if context is None:
            context = self.real_context

        field_renderer = self.get_field_renderer(field_name, context)
        field_renderer.exportable.separator = separator
        return field_renderer.render_value()

    def display_text(self, field_name, context=None):
        if not self.appy_renderer:
            return

        if context is None:
            context = self.real_context

        html_text = self.get_value(field_name)
        display = self.appy_renderer.renderXhtml(html_text)
        return display

    def display_list(self, field_name, separator=', '):
        values = self.get_value(field_name)
        display = separator.join(values)
        return display

    def list(self, field_name):
        values = self.get_value(field_name)
        return values


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
