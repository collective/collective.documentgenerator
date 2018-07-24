# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from plone import api

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_6(Migrator):  # pragma: no cover

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 6 ...')
        self.runProfileSteps('collective.documentgenerator', steps=['typeinfo'], profile='install-base')
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_6(context).run()
