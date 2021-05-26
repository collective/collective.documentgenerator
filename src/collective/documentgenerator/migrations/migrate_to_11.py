# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from plone import api
from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging


logger = logging.getLogger("collective.documentgenerator")


class Migrate_To_11(Migrator):  # pragma: no cover
    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool("portal_catalog")

    def run(self):
        logger.info("Migrating to collective.documentgenerator 11 ...")

        registry = getUtility(IRegistry)
        records = registry.records
        key = "collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.use_stream"

        current_record = api.portal.get_registry_record(key)
        value = True
        if current_record is False:
            value = u"auto"

        record = Record(
            field.Choice(
                title=u"Force communication via in/out stream with LibreOffice.",
                description=(
                    u"If enabled, this will force using stream to communicate witth LibreOffice server. "
                    u"This must be true if the LO server is not on localhost or is in a docker container."
                ),
                vocabulary="collective.documentgenerator.ConfigStream",
            ),
            value=value,
        )
        records[key] = record
        api.portal.set_registry_record(key, value)

        self.finish()


def migrate(context):
    """
    """
    Migrate_To_11(context).run()
