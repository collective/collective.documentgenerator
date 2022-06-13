# -*- coding: utf-8 -*-
from appy.bin.odfclean import Cleaner
from collective.documentgenerator import _
from imio.helpers.security import fplog
from plone import api
from plone.namedfile.file import NamedBlobFile
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope import i18n
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.component.hooks import setSite
from zope.interface import Interface
from zope.interface import Invalid
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import modified

import hashlib
import logging
import os
import re
import tempfile


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
    # Don't use profile now !
    portal = api.portal.getSite()
    ret = []
    for (ppath, ospath) in templates:
        ppath = ppath.strip('/ ')
        obj = portal.unrestrictedTraverse(ppath, default=None)
        if not obj:
            logger.warn("The plone template '%s' was not found" % ppath)
            ret.append((ppath, ospath, 'plone path error'))
            continue
        if not obj.odt_file:
            logger.warn("The plone template '%s' doesn't have odt file" % ppath)
            ret.append((ppath, ospath, 'no odt file'))
            continue
        if not os.path.exists(ospath):
            logger.warn("The template file '%s' doesn't exist" % ospath)
            ret.append((ppath, ospath, 'os path error'))
            continue
        with open(ospath, 'rb') as f:
            data = f.read()
            new_md5 = compute_md5(data)
            if obj.initial_md5 == new_md5:
                ret.append((ppath, ospath, 'unchanged'))
                continue
            elif obj.has_been_modified() and not force:
                ret.append((ppath, ospath, 'kept'))
                continue
            obj.initial_md5 = new_md5
            obj.style_modification_md5 = new_md5
            obj.odt_file.data = data
            modified(obj, Attributes(Interface, 'odt_file'))
            ret.append((ppath, ospath, 'replaced'))
    return ret


def update_dict_with_validation(original_dict, update_dict, error_message=_("Dict update collision on key")):
    for key in update_dict:
        if key in original_dict:
            raise Invalid(_("${error_message} for key = '${key}'",
                            mapping={'error_message': error_message, 'key': key}))

        original_dict[key] = update_dict[key]


def safe_encode(value, encoding='utf-8'):
    """
        Converts a value to encoding, only when it is not already encoded.
    """
    if isinstance(value, unicode):
        return value.encode(encoding)
    return value


def ulocalized_time(date, long_format=None, time_only=None, custom_format=None,
                    domain='plonelocales', target_language=None, context=None,
                    request=None, month_lc=True, day_lc=True):
    """
        Return for a datetime the string value with week and mont translated.
        Take into account %a, %A, %b, %B
    """
    if not custom_format:
        # use toLocalizedTime
        plone = getMultiAdapter((context, request), name=u'plone')
        formatted_date = plone.toLocalizedTime(date, long_format, time_only)
    else:
        from Products.CMFPlone.i18nl10n import monthname_msgid
        from Products.CMFPlone.i18nl10n import monthname_msgid_abbr
        from Products.CMFPlone.i18nl10n import weekdayname_msgid
        from Products.CMFPlone.i18nl10n import weekdayname_msgid_abbr
        if request is None:
            portal = api.portal.get()
            request = portal.REQUEST
        # first replace parts to translate
        custom_format = custom_format.replace('%%', '_p_c_')

        conf = {
            'a': {'fct': weekdayname_msgid_abbr, 'fmt': '%w', 'low': day_lc},
            'A': {'fct': weekdayname_msgid, 'fmt': '%w', 'low': day_lc},
            'b': {'fct': monthname_msgid_abbr, 'fmt': '%m', 'low': month_lc},
            'B': {'fct': monthname_msgid, 'fmt': '%m', 'low': month_lc},
        }
        matches = re.findall(r'%([aAbB])', custom_format)
        for match in sorted(set(matches)):
            # function( int(date.strftime(format) )
            msgid = conf[match]['fct'](int(date.strftime(conf[match]['fmt'])))
            repl = i18n.translate(msgid, domain, context=request, target_language=target_language)
            if conf[match]['low']:
                repl = repl.lower()
            custom_format = re.sub('%{}'.format(match), repl, custom_format)

        # then format date
        custom_format = custom_format.replace('_p_c_', '%%')
        formatted_date = date.strftime(custom_format.encode('utf8'))
    return safe_unicode(formatted_date)


def remove_tmp_file(filename):
    """Do not break if unable to remove temporary file, but log error if any."""
    try:
        os.remove(filename)
    except OSError:
        logger.warn("Could not remove temporary file at {0}".format(filename))


def update_oo_config():
    """ Update config following buildout var """
    key_template = 'collective.documentgenerator.browser.controlpanel.IDocumentGeneratorControlPanelSchema.{}'
    var = {'oo_server': 'OO_SERVER', 'oo_port_list': 'OO_PORT', 'uno_path': 'PYTHON_UNO'}
    for key in var.keys():
        full_key = key_template.format(key)
        configured_oo_option = api.portal.get_registry_record(full_key)
        env_value = os.getenv(var.get(key, 'NO_ONE'), None)
        if env_value:
            new_oo_option = type(configured_oo_option)(os.getenv(var.get(key, 'NO_ONE'), ''))
            if new_oo_option and new_oo_option != configured_oo_option:
                api.portal.set_registry_record(full_key, new_oo_option)
    logger.info("LibreOffice configuration updated for " + getSite().getId())


def update_oo_config_after_bigbang(event):
    setSite(event.object)
    try:
        update_oo_config()
    except Exception:
        logger.error("Update LibreOffice configuration failed", exc_info=1)


def get_site_root_relative_path(obj):
    return "/" + '/'.join(
        getToolByName(obj, 'portal_url').getRelativeContentPath(obj)
    )


def temporary_file_name(suffix=''):
    tmp_dir = os.getenv('CUSTOM_TMP', None)
    if tmp_dir and not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
    return tempfile.mktemp(suffix=suffix, dir=tmp_dir)


def create_temporary_file(initial_file=None, base_name=''):
    tmp_filename = temporary_file_name(suffix=base_name)
    # create the file in any case
    with open(tmp_filename, 'w+') as tmp_file:
        if initial_file:
            tmp_file.write(initial_file.data)
    return tmp_file


def clean_notes(pod_template):
    """ Use appy.pod Cleaner to clean notes (comments). """
    cleaned = 0
    odt_file = pod_template.odt_file
    if odt_file:
        # write file to /tmp to be able to use appy.pod Cleaner
        tmp_file = create_temporary_file(odt_file, '-to-clean.odt')
        cleaner = Cleaner(path=tmp_file.name, verbose=1)
        cleaned = cleaner.run()
        if cleaned:
            manually_modified = pod_template.has_been_modified()
            with open(tmp_file.name, 'rb') as res_file:
                # update template
                result = NamedBlobFile(
                    data=res_file.read(),
                    contentType=odt_file.contentType,
                    filename=pod_template.odt_file.filename)
            pod_template.odt_file = result
            if not manually_modified:
                pod_template.style_modification_md5 = pod_template.current_md5
            extras = 'pod_template={0} cleaned_parts={1}'.format(
                repr(pod_template), cleaned)
            fplog('clean_notes', extras=extras)
        remove_tmp_file(tmp_file.name)

    return bool(cleaned)
