# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IRenamePageStylesSchema
from imio.migrator.migrator import Migrator
from plone import api

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_7(Migrator):  # pragma: no cover

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 7 ...')
        for brain in self.catalog(object_provides=IRenamePageStylesSchema.__identifier__):
            obj = brain.getObject()
            if obj.rename_page_styles is None:
                logger.info("Setting rename_page_styles to false on %s" % brain.getPath())
                obj.rename_page_styles = False
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_7(context).run()
