# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.utils import clean_notes
from imio.migrator.migrator import Migrator
from plone import api

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_13(Migrator):

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def _clean_notes(self):
        """Clean notes of existing POD templates."""
        logger.info('Cleaning notes for existing POD templates...')
        for brain in self.catalog(object_provides=IPODTemplate.__identifier__):
            pod_template = brain.getObject()
            clean_notes(pod_template)
        logger.info('Done.')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 13   ...')
        self._clean_notes()
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_13(context).run()
