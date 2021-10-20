# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IConfigurablePODTemplate
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
        for brain in self.catalog(object_provides=IConfigurablePODTemplate.__identifier__):
            pod_template = brain.getObject()
            # check if stored md5 is still the original value
            md5_original = False
            style_md5_original = False
            if pod_template.current_md5 == pod_template.initial_md5:
                # it is still correct, keep it correct
                md5_original = True
            if pod_template.current_md5 == pod_template.style_modification_md5:
                style_md5_original = True
            # clean and update md5 if it was still the original value
            was_cleaned = clean_notes(pod_template)
            if was_cleaned and md5_original:
                pod_template.initial_md5 = pod_template.current_md5
            if was_cleaned and style_md5_original:
                pod_template.style_modification_md5 = pod_template.current_md5

        logger.info('Done.')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 13   ...')
        self._clean_notes()
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_13(context).run()
