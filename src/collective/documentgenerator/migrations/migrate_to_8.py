# -*- coding: utf-8 -*-

from collective.documentgenerator.content.pod_template import IRenamePageStylesSchema
from imio.migrator.migrator import Migrator
from plone import api
from Products.CMFPlone.utils import base_hasattr

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_8(Migrator):  # pragma: no cover

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 8 ...')
        for brain in self.catalog(object_provides=IRenamePageStylesSchema.__identifier__):
            obj = brain.getObject()
            if base_hasattr(obj, 'rename_page_styles'):
                logger.info("Removing rename_page_styles attribute on %s" % brain.getPath())
                delattr(obj, 'rename_page_styles')
            obj.reindexObject(idxs=['object_provides'])
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_8(context).run()
