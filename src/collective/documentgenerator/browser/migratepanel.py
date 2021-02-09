# -*- coding: utf-8 -*-

from zope import schema, interface, component

from collective.documentgenerator import _
from collective.z3cform.datagridfield import DictRow, DataGridFieldFactory
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from z3c.form import button, form


class IReplaceRowSchema(interface.Interface):
    """
    Schema for DataGridField widget's row of field 'context_variables'
    """
    name = schema.TextLine(
        title=_(u'Search'),
        required=True,
    )

    value = schema.TextLine(
        title=_(u'Replace'),
        required=True,
    )


class IDocumentGeneratorMigratePanelSchema(interface.Interface):
    """
    """
    selected_templates = schema.List(
        title=_(u'heading_available_templates',
                default=u'Available templates'),
        description=_(u'description_available_templates',
                      default=u'The avalaible templates in this Plone site.'),
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(
            source='collective.documentgenerator.AllPODTemplate'
        )
    )
    directives.widget('replacements', DataGridFieldFactory)
    replacements = schema.List(
        title=_(u'Replacements'),
        description=_("The replacements that will be made."),
        required=False,
        value_type=DictRow(
            schema=IReplaceRowSchema,
            required=False
        ),
    )


class DocumentGeneratorMigratePanelAdapter(object):
    interface.implements(IDocumentGeneratorMigratePanelSchema)
    component.adapts(interface.Interface)

    def __init__(self, context):
        self.name = None


class DocumentGeneratorMigratePanelEditForm(AutoExtensibleForm, form.Form):
    schema = IDocumentGeneratorMigratePanelSchema
    label = _(u'Migrate templates')
    description = _(u'')
    preview = {}
    results = {}

    @button.buttonAndHandler(_('Launch'), name="Launch")
    def handle_launch(self, action):
        # TODO do some stuff to execute replacements
        self.results = {
            "Template1": {
                "matched": "self.getItem()",
                "replaced_by": "self.get_grouped()"
            },
            "Template2": {
                "matched": "self.getItem()",
                "replaced_by": "self.get_grouped()"
            }
        }
        return self.render()

    @button.buttonAndHandler(_('Preview'), name="Preview")
    def handle_preview(self, action):
        # TODO do some stuff to execute replacements
        self.preview = {
            "Template1": "self.getItem()",
            "Template2": "self.getItem()",
            "Template3": "self.getItem()",
            "Template4": "self.getItem()",
            "Template5": "self.getItem()",
            "Template6": "self.getItem()",
        }
        return self.render()

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(
            '{context_url}/{view}'.format(
                context_url=self.context.absolute_url(),
                view="@@collective.documentgenerator-controlpanel"
            )
        )


class DocumentGeneratorMigrate(ControlPanelFormWrapper):
    form = DocumentGeneratorMigratePanelEditForm
