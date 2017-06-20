# -*- coding: utf-8 -*-

from appy.pod.renderer import Renderer
from appy.pod.styles_manager import TableProperties

from zope.component import getMultiAdapter
from AccessControl import Unauthorized

from Products.Five import BrowserView
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import normalizeString
from Products.CMFPlone.utils import safe_unicode

from StringIO import StringIO

from collective.documentgenerator import config
from collective.documentgenerator import utils
from collective.documentgenerator.content.pod_template import IPODTemplate
from collective.documentgenerator.interfaces import CyclicMergeTemplatesException
from collective.documentgenerator.interfaces import IDocumentFactory
from collective.documentgenerator.interfaces import PODTemplateNotFoundError

from plone import api

from zope.component import queryAdapter

import mimetypes
import os
import tempfile
from .. import _


class DocumentGenerationView(BrowserView):
    """
    Document generation view.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, template_uid='', output_format=''):
        pod_template, output_format = self._get_base_args(template_uid, output_format)
        return self.generate_and_download_doc(pod_template, output_format)

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
        os.remove(document_path)

        # to avoid problems with long filename we take 120 first characters
        first_part = u'{0}-{1}'.format(pod_template.title, safe_unicode(self.context.Title()))
        filename = '{0}.{1}'.format(normalizeString(first_part), output_format)

        return rendered, filename, gen_context

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

        # enable optimalColumnWidths if enabled in the config
        stylesMapping = {}
        optimalColumnWidths = False
        if config.get_optimize_tables():
            stylesMapping = {'table': TableProperties(optimalColumnWidths=True)}
            optimalColumnWidths = "OCW_.*"

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
            stylesMapping=stylesMapping,
            **kwargs
        )

        # it is only now that we can initialize helper view's appy pod renderer
        if 'view' in generation_context:
            # helper_view has maybe changed in generation context getter
            generation_context['view']._set_appy_renderer(renderer)
        else:
            helper_view._set_appy_renderer(renderer)

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
        generation_context = self.get_base_generation_context()
        utils.update_dict_with_validation(generation_context,
                                          {'context': getattr(helper_view, 'context', None),
                                           'view': helper_view},
                                          _("Error when merging helper_view in generation context"))
        utils.update_dict_with_validation(generation_context, self._get_context_variables(pod_template),
                                          _("Error when merging context_variables in generation context"))
        return generation_context

    def get_base_generation_context(self):
        """
        Override this method to provide your own generation context.
        """
        return {}

    def get_generation_context_helper(self):
        """
        Return the default helper view used for document generation.
        """
        return getMultiAdapter((self.context, self.request), name='document_generation_helper_view')

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
        pod_template, output_format = self._get_base_args(template_uid, output_format)
        persisted_doc = self.generate_persistent_doc(pod_template, output_format)
        self.redirects(persisted_doc)

    def generate_persistent_doc(self, pod_template, output_format):
        """
        Generate a document of format 'output_format' from the template
        'pod_template' and persist it by creating a File containing the
        generated document on the current context.
        """

        doc, doc_name, gen_context = self._generate_doc(pod_template, output_format)

        splitted_name = doc_name.split('.')
        title = '.'.join(splitted_name[:-1])
        extension = splitted_name[-1]

        factory = queryAdapter(self.context, IDocumentFactory)

        #  Bypass any File creation permission of the user. If the user isnt
        #  supposed to save generated document on the site, then its the permission
        #  to call the generation view that should be changed.
        with api.env.adopt_roles(['Manager']):
            persisted_doc = factory.create(doc_file=doc, title=title, extension=extension)

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
