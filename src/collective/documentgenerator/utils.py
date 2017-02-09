# -*- coding: utf-8 -*-

import hashlib
import logging
import os

from zope import i18n
from zope.lifecycleevent import modified
from plone import api

logger = logging.getLogger('collective.documentgenerator')


def translate(msgid, domain='collective.documentgenerator'):
    portal = api.portal.get()
    translation = i18n.translate(
        msgid,
        domain=domain,
        context=portal.REQUEST
    )
    return translation


def compute_md5(data):
    md5 = hashlib.md5(data).hexdigest()
    return md5


def update_templates(templates, profile='', force=False):
    """
        script to manage templates update.
        # see http://trac.imio.be/trac/ticket/9383 for full implementation
        :param list templates: list of tuples containing ('plone-template-path', 'os-template-path')
        :param str profile: profile path stored on template (or various identification)
        :param bool force: force overrides of templates
    """
    # Don't use profile now
    # Don't use has_been_modified method now (incorrect)
    # Don't use is_modified or current_md5
    portal = api.portal.getSite()
    for (ppath, ospath) in templates:
        ppath = ppath.strip('/ ')
        obj = portal.unrestrictedTraverse(ppath, default=None)
        if not obj:
            logger.warn("The plone template '%s' was not found" % ppath)
            continue
        if not os.path.exists(ospath):
            logger.warn("The template file '%s' doesn't exist" % ospath)
            continue
        with open(ospath, 'rb') as f:
            data = f.read()
            new_md5 = compute_md5(data)
            if obj.initial_md5 == new_md5:
                continue
            obj.odt_file.data = data
            obj.initial_md5 = new_md5
            modified(obj)
