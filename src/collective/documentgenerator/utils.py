# -*- coding: utf-8 -*-
from appy.bin.odfclean import Cleaner
from appy.pod.lo_pool import LoPool
from appy.pod.renderer import Renderer
from collective.documentgenerator import _
from collective.documentgenerator import BLDT_DIR
from collective.documentgenerator import config
from collective.documentgenerator.config import DEFAULT_OO_PORT
from collective.documentgenerator.config import get_oo_port_list
from collective.documentgenerator.config import get_oo_server
from collective.documentgenerator.config import get_uno_path
from imio.helpers.content import uuidToObject
from imio.helpers.security import fplog
from imio.pyutils.system import runCommand
from plone import api
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobFile
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope import i18n
from zope.annotation import IAnnotations
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


def convert_odt(afile, output_name, fmt='pdf', **kwargs):
    """
    Convert an odt file to another format using appy.pod.

    :param afile: file field content like NamedBlobFile
    :param output_name: output name
    :param fmt: output format, default to 'pdf'
    :param kwargs: other parameters passed to Renderer, i.e pdfOptions='ExportNotes=True;SelectPdfVersion=1'
    """
    lo_pool = LoPool.get(
        python=config.get_uno_path(),
        server=config.get_oo_server(),
        port=config.get_oo_port_list(),
    )
    if not lo_pool:
        raise Exception("Could not find LibreOffice, check your configuration")

    temp_file = create_temporary_file(afile, '.odt')
    converted_filename = None
    try:
        renderer = Renderer(
            temp_file.name,
            afile,
            temporary_file_name(suffix=".{extension}".format(extension=fmt)),
            **kwargs
        )

        lo_pool(renderer, temp_file.name, fmt)
        converted_filename = temp_file.name.replace('.odt', '.{}'.format(fmt))
        if not os.path.exists(converted_filename):
            api.portal.show_message(
                message=_(u"Conversion failed, no converted file '{}'".format(safe_unicode(output_name))),
                request=getSite().REQUEST,
                type="error",
            )
            raise Invalid(u"Conversion failed, no converted file '{}'".format(safe_unicode(output_name)))
        with open(converted_filename, 'rb') as f:
            converted_file = f.read()
    finally:
        remove_tmp_file(temp_file.name)
        if converted_filename:
            remove_tmp_file(converted_filename)

    return output_name, converted_file


def convert_file(afile, output_name, fmt="pdf", renderer=False):
    """
    Convert a file to another libreoffice readable format using appy.pod

    :param afile: file field content like NamedBlobFile
    :param output_name: output name
    :param fmt: output format, default to "pdf"
    :param renderer: whether to use appy.pod Renderer or converter script. Default to False.
    """
    if renderer:
        if not afile.filename.endswith('.odt'):
            message = _(u"Conversion with renderer only works from odt files.")
            raise Invalid(message)
        return convert_odt(afile, output_name, fmt=fmt)
    from appy.pod import converter
    converter_path = converter.__file__.endswith(".pyc") and converter.__file__[:-1] or converter.__file__
    file_ext = afile.filename.split('.')[-1].lower()
    temp_file = create_temporary_file(afile, base_name=".{}".format(file_ext))
    converted_filename = temp_file.name.replace(".{}".format(file_ext), ".{}".format(fmt))
    converted_file = ""
    try:
        ports = get_oo_port_list()
        port = ports[0] if ports else DEFAULT_OO_PORT
        command = "{python_uno_path} {converter_path} {temp_file} {fmt} -p {port} -e {server}".format(
            python_uno_path=get_uno_path(), converter_path=converter_path, temp_file=temp_file.name, fmt=fmt,
            port=port, server=get_oo_server())
        out, err, code = runCommand(command)
        # This command has no output on success
        if code != 0 or err or not os.path.exists(converted_filename):
            message = _(u"Conversion failed, no converted file '{}'".format(safe_unicode(output_name)))
            raise Invalid(message)
        with open(converted_filename, 'rb') as f:
            converted_file = f.read()
    except Exception as e:
        api.portal.show_message(message=str(e), request=getSite().REQUEST, type="error")
    finally:
        remove_tmp_file(temp_file.name)
        if os.path.exists(converted_filename):
            remove_tmp_file(converted_filename)
    return output_name, converted_file


def convert_and_save_file(afile, container, portal_type, output_name, fmt='pdf', from_uid=None, attributes=None, renderer=False):
    """
    Convert a file to another libreoffice readable format using appy.pod and save it in a NamedBlobFile.

    :param afile: file field content like NamedBlobFile
    :param container: container object to create new file
    :param portal_type: portal type
    :param output_name: output name
    :param fmt: output format, default to 'pdf'
    :param from_uid: uid from original file object
    :param attributes: dict of other attributes to set on created content
    :param renderer: whether to use appy.pod Renderer or converter script. Default to False.
    """
    converted_filename, converted_file = convert_file(afile, output_name, fmt=fmt, renderer=renderer)
    file_object = NamedBlobFile(converted_file, filename=safe_unicode(converted_filename))
    if attributes is None:
        attributes = {}
    attributes["conv_from_uid"] = from_uid
    new_file = createContentInContainer(
        container,
        portal_type,
        title=converted_filename,
        file=file_object,
        **attributes)
    if from_uid:
        annot = IAnnotations(new_file)
        annot["documentgenerator"] = {"conv_from_uid": from_uid}
    return new_file


@api.env.mutually_exclusive_parameters("document", "document_uid")
def need_mailing_value(document=None, document_uid=None):
    if not document:
        document = uuidToObject(document_uid, unrestricted=True)
    annot = IAnnotations(document)
    if "documentgenerator" in annot and annot["documentgenerator"].get("need_mailing", False):
        return True
    return False


def odfsplit(content):
    """Splits an ODT document into a series of sub-documents. The split is based on page breaks.

    :param content: The binary content of the ODT file to be split.
    :return: A tuple containing the exit code, a generator yielding the binary content of each subfile and
             the number of files
    """

    def get_subfiles(temp_file, nb_files):
        if nb_files == 1:
            with open(temp_file, "rb") as f:
                yield f.read()
            remove_tmp_file(temp_file)
            return
        for i in range(1, nb_files + 1):
            subfile = temp_file.replace(".odt", ".{}.odt".format(i))
            with open(subfile, "rb") as sf:
                yield sf.read()
            remove_tmp_file(subfile)
        remove_tmp_file(temp_file)

    temp_file = temporary_file_name(suffix=".odt")
    with open(temp_file, "wb") as f:
        f.write(content)
    command = "{pwd}/bin/odfsplit {temp_file}".format(temp_file=temp_file, pwd=BLDT_DIR)
    out, err, code = runCommand(command)
    nb_files = 0
    if out and code == 0:
        part0 = out[0].split(" ")[0]  # Ex: "2 files were generated."
        if part0.isdigit():
            nb_files = int(part0)
            value = get_subfiles(temp_file, nb_files)
        else:
            nb_files = 1
            value = get_subfiles(temp_file, 1)
    else:
        value = "".join(err)
    return code, value, nb_files
