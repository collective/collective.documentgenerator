# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from imio.migrator.migrator import Migrator
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_9(Migrator):  # pragma: no cover

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 9 ...')
        for brain in self.catalog(object_provides=IConfigurablePODTemplate.__identifier__):
            obj = brain.getObject()
            if hasattr(obj, 'optimize_tables'):
                if obj.optimize_tables:
                    obj.column_modifier = 'optimize'
                delattr(obj, 'optimize_tables')

        optimize_tables_registry_key = 'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.optimize_tables'
        column_modifier_registry_key = 'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.column_modifier'

        registry = getUtility(IRegistry)
        optimize_tables = api.portal.get_registry_record(optimize_tables_registry_key, default=None)

        if optimize_tables:
            api.portal.set_registry_record(column_modifier_registry_key, 'optimize')

        if optimize_tables_registry_key in registry.records:
            del registry.records[optimize_tables_registry_key]

        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_9(context).run()
