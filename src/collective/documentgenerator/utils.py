# -*- coding: utf-8 -*-

import hashlib
import logging
import os

from zope import i18n
from zope.lifecycleevent import modified
from plone import api
from Products.CMFPlone.utils import base_hasattr

from zope.interface import Invalid

from . import _

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
        function to manage templates update.
        # see http://trac.imio.be/trac/ticket/9383 for full implementation
        :param list templates: list of tuples containing ('plone-template-path', 'os-template-path')
        :param str profile: profile path stored on template (or various identification)
        :param bool force: force overrides of templates
    """
    # Don't use profile now
    # Don't use has_been_modified method now (incorrect)
    # Don't use is_modified or current_md5
    portal = api.portal.getSite()
    ret = []
    for (ppath, ospath) in templates:
        ppath = ppath.strip('/ ')
        obj = portal.unrestrictedTraverse(ppath, default=None)
        if not obj:
            logger.warn("The plone template '%s' was not found" % ppath)
            ret.append((ppath, ospath, 'plone path error'))
            continue
        if not os.path.exists(ospath):
            logger.warn("The template file '%s' doesn't exist" % ospath)
            ret.append((ppath, ospath, 'os path error'))
            continue
        with open(ospath, 'rb') as f:
            data = f.read()
            if base_hasattr(obj, 'initial_md5'):
                new_md5 = compute_md5(data)
                if obj.initial_md5 == new_md5:
                    ret.append((ppath, ospath, 'unchanged'))
                    continue
                obj.initial_md5 = new_md5
            elif not force:
                ret.append((ppath, ospath, 'unchanged'))
                continue
            obj.odt_file.data = data
            modified(obj)
            ret.append((ppath, ospath, 'replaced'))
    return ret


def update_dict_with_validation(original_dict, update_dict, error_message=_("Dict update collision on key")):
    for key in update_dict:
        if key in original_dict:
            raise Invalid(_("${error_message} for key = '${key}'", mapping={'error_message': error_message, 'key': key}))

        original_dict[key] = update_dict[key]
