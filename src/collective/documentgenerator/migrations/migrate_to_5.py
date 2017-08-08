# -*- coding: utf-8 -*-

import logging
from imio.migrator.migrator import Migrator
from plone import api
from collective.documentgenerator.content.pod_template import POD_TEMPLATE_TYPES

logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_5(Migrator):  # pragma: no cover

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 5 ...')
        self.runProfileSteps('collective.documentgenerator', steps=['typeinfo'], profile='install-base')
        for brain in self.catalog(portal_type=POD_TEMPLATE_TYPES.values()):
            brain.getObject().reindexObject(idxs=['getIcon'])
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_5(context).run()
