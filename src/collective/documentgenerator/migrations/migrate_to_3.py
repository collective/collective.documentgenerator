# -*- coding: utf-8 -*-

import logging
from imio.migrator.migrator import Migrator
from plone import api

logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_3(Migrator):

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 3 ...')
        for brain in self.catalog(portal_type='ConfigurablePODTemplate'):
            obj = brain.getObject()
            if obj.merge_templates:
                newvalue = []
                for line in obj.merge_templates:
                    if 'do_rendering' not in line:
                        line['do_rendering'] = True
                    newvalue.append(line)
                obj.merge_templates = newvalue
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_3(context).run()
