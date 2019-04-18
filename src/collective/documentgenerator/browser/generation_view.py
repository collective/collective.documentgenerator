# -*- coding: utf-8 -*-

import mimetypes
import tempfile
import unicodedata
from StringIO import StringIO

import pkg_resources
from AccessControl import Unauthorized
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from appy.pod.renderer import Renderer
from appy.pod.styles_manager import TableProperties
from collective.documentgenerator import config
from collective.documentgenerator import utils
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.interfaces import CyclicMergeTemplatesException
from collective.documentgenerator.interfaces import IDocumentFactory
from collective.documentgenerator.interfaces import PODTemplateNotFoundError
from collective.documentgenerator.utils import remove_tmp_file
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.i18n.normalizer.interfaces import IFileNameNormalizer
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter
from zope.component import queryAdapter
from zope.component import queryUtility
from .. import _

HAS_FINGERPOINTING = None

try:
    pkg_resources.get_distribution('collective.fingerpointing')
except pkg_resources.DistributionNotFound:
    HAS_FINGERPOINTING = False
else:
    HAS_FINGERPOINTING = True

class DocumentGenerationView(BrowserView):
    """
    Document generation view.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.pod_template = None
        self.output_format = None

    def __call__(self, template_uid='', output_format=''):
        self.pod_template, self.output_format = self._get_base_args(template_uid, output_format)
        return self.generate_and_download_doc(self.pod_template, self.output_format)

    def _get_base_args(self, template_uid, output_format):
        template_uid = template_uid or self.get_pod_template_uid()
        pod_template = self.get_pod_template(template_uid)
        output_format = output_format or self.get_generation_format()
        if not output_format:
            raise Exception("No 'output_format' found to generate this document")

        return pod_template, output_format

    def generate_and_download_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template' and return it as a downloadable file.
        """
        if HAS_FINGERPOINTING:
            from collective.fingerpointing.config import AUDIT_MESSAGE
            from collective.fingerpointing.logger import log_info
            from collective.fingerpointing.utils import get_request_information
            # add logging message to fingerpointing log
            user, ip = get_request_information()
            action = 'generate_document'
            extras = 'context={0} pod_template={1} output_format={2}'.format(
                '/'.join(self.context.getPhysicalPath()),
                '/'.join(pod_template.getPhysicalPath()),
                output_format)
            log_info(AUDIT_MESSAGE.format(user, ip, action, extras))

        doc, doc_name, gen_context = self._generate_doc(pod_template, output_format)
        self._set_header_response(doc_name)
        return doc

    def _generate_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template'.
        """
        if not pod_template.can_be_generated(self.context):
            raise Unauthorized('You are not allowed to generate this document.')

        if output_format not in pod_template.get_available_formats():
            raise Exception(
                "Asked output format '{0}' "
                "is not available for template '{1}'!".format(
                    output_format,
                    pod_template.getId()
                )
            )

        # subtemplates should not refer to each other in a cyclic way.
        self._check_cyclic_merges(pod_template)

        # Recursive generation of the document and all its subtemplates.
        document_path, gen_context = self._recursive_generate_doc(pod_template, output_format)

        rendered_document = open(document_path, 'rb')
        rendered = rendered_document.read()
        rendered_document.close()
        remove_tmp_file(document_path)
        filename = self._get_filename()
        return rendered, filename, gen_context

    def _get_filename(self):
        """ """
        # we limit filename to 120 characters
        first_part = u'{0} {1}'.format(self.pod_template.title, safe_unicode(self.context.Title()))
        # replace unicode special characters with ascii equivalent value
        first_part = unicodedata.normalize('NFKD', first_part).encode('ascii', 'ignore')
        util = queryUtility(IFileNameNormalizer)
        # remove '-' from first_part because it is handled by cropName that manages max_length
        # and it behaves weirdly if it encounters '-'
        # moreover avoid more than one blank space at a time
        first_part = u' '.join(util.normalize(first_part).replace(u'-', u' ').split()).strip()
        filename = '{0}.{1}'.format(util.normalize(first_part, max_length=120), self.output_format)
        return filename

    def _recursive_generate_doc(self, pod_template, output_format):
        """
        Generate a document recursively by starting to generate all its
        subtemplates before merging them in the final document.
        Return the file path of the generated document.
        """
        sub_templates = pod_template.get_templates_to_merge()
        sub_documents = {}
        for context_name, (sub_pod, do_rendering) in sub_templates.iteritems():
            # Force the subtemplate output_format to 'odt' because appy.pod
            # can only merge documents in this format.
            if do_rendering:
                sub_documents[context_name] = self._recursive_generate_doc(
                    pod_template=sub_pod,
                    output_format='odt'
                )[0]
            else:
                sub_documents[context_name] = sub_pod

        document_path, gen_context = self._render_document(pod_template, output_format, sub_documents)

        return document_path, gen_context

    def get_pod_template(self, template_uid):
        """
        Return the default PODTemplate that will be used when calling
        this view.
        """
        catalog = api.portal.get_tool('portal_catalog')

        template_brains = catalog.unrestrictedSearchResults(
            object_provides=IPODTemplate.__identifier__,
            UID=template_uid
        )
        if not template_brains:
            raise PODTemplateNotFoundError(
                "Couldn't find POD template with UID '{0}'".format(template_uid)
            )

        template_path = template_brains[0].getPath()
        pod_template = self.context.unrestrictedTraverse(template_path)
        return pod_template

    def get_pod_template_uid(self):
        template_uid = self.request.get('template_uid', '')
        return template_uid

    def get_generation_format(self):
        """
        Return the default document output format that will be used
        when calling this view.
        """
        output_format = self.request.get('output_format')
        return output_format

    def _render_document(self, pod_template, output_format, sub_documents, raiseOnError=False, **kwargs):
        """
        Render a single document of type 'output_format' using the odt file
        'document_template' as the generation template.
        Subdocuments is a dictionnary of previously generated subtemplate
        that will be merged into the current generated document.
        """
        document_template = pod_template.get_file()
        temp_filename = tempfile.mktemp('.{extension}'.format(extension=output_format))

        # Prepare rendering context
        helper_view = self.get_generation_context_helper()
        generation_context = self._get_generation_context(helper_view, pod_template=pod_template)

        # enrich the generation context with previously generated documents
        utils.update_dict_with_validation(generation_context, sub_documents,
                                          _("Error when merging merge_templates in generation context"))

        # enable optimalColumnWidths if enabled in the config and/or on ConfigurablePodTemplate
        stylesMapping = {}
        optimalColumnWidths = "OCW_.*"
        distributeColumns = "DC_.*"

        column_modifier = pod_template.get_column_modifier()
        if column_modifier == -1:
            column_modifier = config.get_column_modifier()

        if column_modifier == 'disabled':
            optimalColumnWidths = False
            distributeColumns = False
        else:
            stylesMapping = {
                'table': TableProperties(columnModifier=column_modifier != 'nothing' and column_modifier or None)}

        # if raiseOnError is not enabled, enabled it in the config excepted if user is a Manager
        # and currently generated document use odt format
        if not raiseOnError:
            if config.get_raiseOnError_for_non_managers():
                raiseOnError = True
                if 'Manager' in api.user.get_roles() and output_format == 'odt':
                    raiseOnError = False

        renderer = Renderer(
            StringIO(document_template.data),
            generation_context,
            temp_filename,
            pythonWithUnoPath=config.get_uno_path(),
            ooPort=config.get_oo_port(),
            raiseOnError=raiseOnError,
            imageResolver=api.portal.get(),
            forceOoCall=True,
            optimalColumnWidths=optimalColumnWidths,
            distributeColumns=distributeColumns,
            stylesMapping=stylesMapping,
            **kwargs
        )

        # it is only now that we can initialize helper view's appy pod renderer
        all_helper_views = self.get_views_for_appy_renderer(generation_context, helper_view)
        for view in all_helper_views:
            view._set_appy_renderer(renderer)

        renderer.run()

        # return also generation_context to test ist content in tests
        return temp_filename, generation_context

    def _get_context_variables(self, pod_template):
        if base_hasattr(pod_template, 'get_context_variables'):
            return pod_template.get_context_variables()
        return {}

    def _get_generation_context(self, helper_view, pod_template):
        """
        Return the generation context for the current document.
        """
        generation_context = self.get_base_generation_context(helper_view, pod_template)
        utils.update_dict_with_validation(generation_context,
                                          {'context': getattr(helper_view, 'context', None),
                                           'view': helper_view},
                                          _("Error when merging helper_view in generation context"))
        utils.update_dict_with_validation(generation_context, self._get_context_variables(pod_template),
                                          _("Error when merging context_variables in generation context"))
        return generation_context

    def get_base_generation_context(self, helper_view, pod_template):
        """
        Override this method to provide your own generation context.
        """
        return {}

    def get_generation_context_helper(self):
        """
        Return the default helper view used for document generation.
        """
        helper_view = getMultiAdapter((self.context, self.request), name='document_generation_helper_view')
        helper_view.pod_template = self.pod_template
        helper_view.output_format = self.output_format
        return helper_view

    def get_views_for_appy_renderer(self, generation_context, helper_view):
        views = []
        if 'view' in generation_context:
            # helper_view has maybe changed in generation context getter
            views.append(generation_context['view'])
        else:
            views.append(helper_view)

        return views

    def _set_header_response(self, filename):
        """
        Tell the browser that the resulting page contains ODT.
        """
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader(
            'Content-disposition',
            u'inline;filename="{}"'.format(filename).encode('utf-8')
        )

    def _check_cyclic_merges(self, pod_template):
        """
        Check if the template 'pod_template' has subtemplates referring to each
        other in a cyclic way.
        """

        def traverse_check(pod_template, path):

            if pod_template in path:
                path.append(pod_template)
                start_cycle = path.index(pod_template)
                start_msg = ' --> '.join(
                    ['"{}" {}'.format(t.Title(), '/'.join(t.getPhysicalPath())) for t in path[:start_cycle]]
                )
                cycle_msg = ' <--> '.join(
                    ['"{}" {}'.format(t.Title(), '/'.join(t.getPhysicalPath())) for t in path[start_cycle:]]
                )
                msg = '{} -> CYCLE:\n{}'.format(start_msg, cycle_msg)
                raise CyclicMergeTemplatesException(msg)

            new_path = list(path)
            new_path.append(pod_template)

            sub_templates = pod_template.get_templates_to_merge()

            for name, (sub_template, do_rendering) in sub_templates.iteritems():
                traverse_check(sub_template, new_path)

        traverse_check(pod_template, [])


class PersistentDocumentGenerationView(DocumentGenerationView):
    """
    Persistent document generation view.
    """

    def __call__(self, template_uid='', output_format=''):
        self.pod_template, self.output_format = self._get_base_args(template_uid, output_format)
        persisted_doc = self.generate_persistent_doc(self.pod_template, self.output_format)
        self.redirects(persisted_doc)

    def add_mailing_infos(self, doc, gen_context):
        """ store mailing informations on generated doc """
        annot = IAnnotations(doc)
        if 'mailed_data' in gen_context or 'mailing_list' in gen_context:
            annot['documentgenerator'] = {'need_mailing': False}
        else:
            annot['documentgenerator'] = {'need_mailing': True, 'template_uid': self.pod_template.UID(),
                                          'output_format': self.output_format, 'context_uid': self.context.UID()}

    def _get_title(self, doc_name, gen_context):
        splitted_name = doc_name.split('.')
        title = self.pod_template.title
        extension = splitted_name[-1]
        return safe_unicode(title), extension

    def generate_persistent_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template' and persist it by creating a File containing the
        generated document on the current context.
        """

        doc, doc_name, gen_context = self._generate_doc(pod_template, output_format)

        title, extension = self._get_title(doc_name, gen_context)

        factory = queryAdapter(self.context, IDocumentFactory)

        #  Bypass any File creation permission of the user. If the user isnt
        #  supposed to save generated document on the site, then its the permission
        #  to call the generation view that should be changed.
        with api.env.adopt_roles(['Manager']):
            persisted_doc = factory.create(doc_file=doc, title=title, extension=extension)

        # store informations on persisted doc
        self.add_mailing_infos(persisted_doc, gen_context)

        return persisted_doc

    def redirects(self, persisted_doc):
        """
        Redirects to the created document.
        """
        if config.HAS_PLONE_5:
            filename = persisted_doc.file.filename
        else:
            filename = persisted_doc.getFile().filename
        self._set_header_response(filename)
        response = self.request.response
        return response.redirect(persisted_doc.absolute_url() + '/external_edit')

    def mailing_related_generation_context(self, helper_view, gen_context):
        """
            Add mailing related information in generation context
        """
        # We add mailed_data if we have only one element in mailing list
        mailing_list = helper_view.mailing_list(gen_context)
        if len(mailing_list) == 0:
            utils.update_dict_with_validation(gen_context, {'mailed_data': None},
                                              _("Error when merging mailed_data in generation context"))
        elif len(mailing_list) == 1:
            utils.update_dict_with_validation(gen_context, {'mailed_data': mailing_list[0]},
                                              _("Error when merging mailed_data in generation context"))

    def _get_generation_context(self, helper_view, pod_template):
        """ """
        gen_context = super(PersistentDocumentGenerationView, self)._get_generation_context(helper_view, pod_template)
        self.mailing_related_generation_context(helper_view, gen_context)
        return gen_context


class MailingLoopPersistentDocumentGenerationView(PersistentDocumentGenerationView):
    """
        Mailing persistent document generation view.
        This view use a MailingLoopTemplate to loop on a document when replacing some variables in.
    """

    def __call__(self, document_uid='', document_url_path=''):
        document_uid = document_uid or self.request.get('document_uid', '')
        document_url_path = document_url_path or self.request.get('document_url_path', '')
        if not document_uid and not document_url_path:
            raise Exception("No 'document_uid' or 'url_path' found to generate this document")
        elif document_url_path:
            site = api.portal.get()
            self.document = site.restrictedTraverse(document_url_path)
        else:
            self.document = uuidToObject(document_uid)
        if not self.document:
            raise Exception("Cannot find document with UID '{0}'".format(document_uid))
        self.pod_template, self.output_format = self._get_base_args('', '')
        persisted_doc = self.generate_persistent_doc(self.pod_template, self.output_format)
        self.redirects(persisted_doc)

    def _get_base_args(self, template_uid, output_format):
        annot = IAnnotations(self.document).get('documentgenerator', '')
        if not annot or 'template_uid' not in annot:
            raise Exception("Cannot find 'template_uid' on document '{0}'".format(self.document.absolute_url()))
        self.orig_template = self.get_pod_template(annot['template_uid'])
        if (not base_hasattr(self.orig_template, 'mailing_loop_template') or
                not self.orig_template.mailing_loop_template):
            raise Exception("Cannot find 'mailing_loop_template' on template '{0}'".format(
                            self.orig_template.absolute_url()))
        loop_template = self.get_pod_template(self.orig_template.mailing_loop_template)

        if 'output_format' not in annot:
            raise Exception("No 'output_format' found to generate this document")
        return loop_template, annot['output_format']

    def mailing_related_generation_context(self, helper_view, gen_context):
        """
            Add mailing related information in generation context
        """
        # We do nothing here because we have to call mailing_list after original template context variable inclusion

    def _get_generation_context(self, helper_view, pod_template):
        """ """
        gen_context = super(MailingLoopPersistentDocumentGenerationView, self). \
            _get_generation_context(helper_view, pod_template)
        # add variable context from original template
        utils.update_dict_with_validation(gen_context, self._get_context_variables(self.orig_template),
                                          _("Error when merging context_variables in generation context"))
        # add mailing list in generation context
        dic = {'mailing_list': helper_view.mailing_list(gen_context), 'mailed_doc': self.document}
        utils.update_dict_with_validation(gen_context, dic,
                                          _("Error when merging mailing_list in generation context"))
        return gen_context
