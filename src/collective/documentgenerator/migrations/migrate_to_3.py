# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
from imio.migrator.migrator import Migrator
from plone import api

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_3(Migrator):  # pragma: no cover

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 3 ...')
        for brain in self.catalog(object_provides=IConfigurablePODTemplate.__identifier__):
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
