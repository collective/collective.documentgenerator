# -*- coding: utf-8 -*-

from collections import OrderedDict
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.search_replace.pod_template import SearchAndReplacePODTemplates
from imio.helpers.content import uuidToObject
from imio.migrator.migrator import Migrator
from imio.pyutils.utils import safe_encode
from plone import api

import logging


logger = logging.getLogger('collective.documentgenerator')


class Migrate_To_16(Migrator):

    def __init__(self, context):
        Migrator.__init__(self, context)
        self.catalog = api.portal.get_tool('portal_catalog')

    def _clean_expr(self):
        """Clean expressions of existing POD templates."""
        logger.info('Cleaning expressions for existing POD templates...')
        results = []
        for brain in self.catalog(object_provides=IPODTemplate.__identifier__):
            pod_template = brain.getObject()
            with SearchAndReplacePODTemplates([pod_template]) as search_replace:
                res = search_replace.replace('_underscored_', '++REPLACED++', is_regex=False)
                if res:
                    results.append(res)
            with SearchAndReplacePODTemplates([pod_template]) as search_replace:
                res = search_replace.replace('_banned_', '++REPLACED++', is_regex=False)
                if res:
                    results.append(res)
        # format results and dump it in the Zope log
        # as clean as possible so it can be used to know what changed
        data = {}
        for result in results:
            pt_uid, infos = result.items()[0]
            pt = uuidToObject(pt_uid, unrestricted=True)
            pt_path_and_title = "{0} - {1}".format(
                '/'.join(pt.getPhysicalPath()), pt.Title())
            if pt_path_and_title not in data:
                data[pt_path_and_title] = []
                self.warnings.append('Replacements were done in POD template at %s'
                                     % pt_path_and_title)
            for info in infos:
                # collective.documentgenerator < 3.30 from which we use appy.pod S&R
                # XXX to be removed when using collective.documentgenerator >= 3.30
                if hasattr(info, 'pod_expr'):
                    data[pt_path_and_title].append("---- " + info.pod_expr)
                    data[pt_path_and_title].append("++++ " + info.new_pod_expr)
                else:
                    line = repr(info).replace('  These changes were done:', '>>>'). \
                        replace('\n\n', '\n').rstrip('\n')
                    data[pt_path_and_title].append(line)
        logger.info("REPLACEMENTS IN POD TEMPLATES")
        if not data:
            logger.info("=============================")
            logger.info("No replacement was done.")
        else:
            # order data by pt_path
            ordered_data = OrderedDict(sorted(data.items()))
            output = ["============================="]
            for pt_path_and_title, infos in ordered_data.items():
                output.append('\n')
                output.append("POD template " + pt_path_and_title)
                output.append('-' * len("POD template " + pt_path_and_title))
                for info in infos:
                    output.append(info)
                output.append('\n')
            # make sure we do not mix unicode and utf-8
            fixed_output = []
            for line in output:
                line = safe_encode(line)
                fixed_output.append(line)
            logger.info('\n'.join(fixed_output))
        logger.info('Done.')

    def run(self):
        logger.info('Migrating to collective.documentgenerator 16...')
        self._clean_expr()
        self.finish()


def migrate(context):
    '''
    '''
    Migrate_To_16(context).run()
