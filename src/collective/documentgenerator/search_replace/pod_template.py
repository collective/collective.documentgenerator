from collective.documentgenerator.browser.generation_view import HAS_FINGERPOINTING
from collective.documentgenerator.search_replace.utils import SearchAndReplacePODTemplateFiles
from collective.documentgenerator.utils import get_site_root_relative_path
from plone.namedfile import NamedBlobFile

import collections
import mimetypes
import os
import re


SearchReplaceResult = collections.namedtuple(
    "SearchReplaceResult", ["pod_expr", "match_start", "match_end", "match", "node_type", "new_pod_expr"]
)


class SearchAndReplacePODTemplates:
    """
    Search and replace POD expression among PODTemplates.
    Use it like this:
        with SearchAndReplacePODTemplates(podtemplate_obj) as search_replace:
            search_results = search_replace.search('WhatISearch')
            replace_results = search_replace.replace('^WillBeReplaced$', 'ByThis', is_regex=True)
    """

    def __init__(self, podtemplates):
        """
        :param podtemplates: List of PODTemplate objects
        """
        self.podtemplates = podtemplates
        self.templates_by_filename = {}
        self.tmp_dir = "/tmp/docgen"
        self.changed_files = set()

        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        # compute the (future) file system path of the plone pod templates
        for podtemplate in podtemplates:
            if not podtemplate.odt_file:
                continue  # ignore templates referring another pod template.
            if (podtemplate.odt_file.filename or podtemplate.id).split(".")[-1].lower() != "odt":
                continue  # ignore templates that are not odt file.
            template_path = get_site_root_relative_path(podtemplate)
            extension = mimetypes.guess_extension(podtemplate.odt_file.filename or '') or ''
            fs_filename = "{}/{}{}".format(self.tmp_dir, template_path.replace("/", "_"), extension)
            self.templates_by_filename[fs_filename] = {"obj": podtemplate, "path": template_path}

    def __enter__(self):
        """
        copy the plone pod template content on the file system
        """
        for filename in self.templates_by_filename.keys():
            # clean old files
            if os.path.isfile(filename):
                os.remove(filename)
            # copy the pod templates on the file system.
            template_file = open(filename, "w")
            plone_template = self.templates_by_filename[filename]["obj"]
            template_file.write(plone_template.odt_file.data)
            template_file.close()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # push the result back into the site pod templates
        for filename in self.changed_files:
            with open(filename, "rb") as replaced_file:
                podtemplate = self.templates_by_filename[filename]["obj"]
                result = NamedBlobFile(
                    data=replaced_file.read(),
                    contentType=podtemplate.odt_file.contentType or mimetypes.guess_type(filename)[0],
                    filename=podtemplate.odt_file.filename,
                )
                podtemplate.odt_file = result
        # clean tmp file
        for filename in self.templates_by_filename.keys():
            if os.path.isfile(filename):
                os.remove(filename)

    def search(self, find_expr, is_regex=False):
        """
        Search find_expr in self.podtemplates
        :param find_expr: A regex str or simple string
        :param is_regex: use is_regex=False if find_expr is not a regex
        :return: a dict with podtemplate uid as key and list of SearchReplaceResult as value
        """
        if not is_regex:
            find_expr = re.escape(find_expr)
        regex = re.compile(find_expr)

        search_files_results = SearchAndReplacePODTemplateFiles(
            find_expr="", filenames_expr=self.templates_by_filename.keys(), replace=None, silent=True, backup=False
        ).search(regex, self.templates_by_filename.keys())

        results = self._prepare_results_output(search_files_results, is_replacing=False)
        return results

    def replace(self, find_expr, replace_expr, is_regex=False):
        """
        Replace find_expr match with replace_expr in self.podtemplates
        :param find_expr: A regex str or simple str
        :param replace_expr: A str that will replace find_expr match
        :param is_regex: use is_regex=False if find_expr is not a regex
        :return: a dict with podtemplate uid as key and list of SearchReplaceResult as value
        """
        if not is_regex:
            find_expr = re.escape(find_expr)
        regex = re.compile(find_expr)

        search_files_results = SearchAndReplacePODTemplateFiles(
            find_expr="", filenames_expr=self.templates_by_filename.keys(), replace=None, silent=True, backup=False
        ).search(regex, self.templates_by_filename.keys())

        results = self._prepare_results_output(search_files_results, replace_expr)

        new_files = SearchAndReplacePODTemplateFiles(
            find_expr=regex,
            filenames_expr=self.templates_by_filename.keys(),
            replace=replace_expr,
            silent=True,
            backup=False,
        ).replace(regex, replace_expr, search_files_results, target_dir=None)

        for new_file in new_files:
            self.changed_files.add(new_file.filename)
        return results

    def _prepare_results_output(self, search_files_results, replace_expr="", is_replacing=True):
        """ Prepare results output so we have a nice feedback when searching and replacing """
        results = {}
        for file_path, file_results in search_files_results.items():
            template = self.templates_by_filename[file_path]["obj"]
            template_uid = template.UID()
            results[template_uid] = []
            for sub_file, sub_file_results in file_results.items():
                for file_result in sub_file_results[1]:
                    pod_expr = file_result["XMLnode"].data
                    for match in file_result["matches"]:
                        match_str = pod_expr[match.start(): match.end()]
                        new_pod_expr = pod_expr[: match.start()] + replace_expr + pod_expr[match.end():]
                        results[template_uid].append(
                            SearchReplaceResult(
                                match=match_str,
                                pod_expr=pod_expr,
                                match_start=match.start(),
                                match_end=match.end(),
                                node_type=file_result["node_type"],
                                new_pod_expr=new_pod_expr,
                            )
                        )
                        if is_replacing:
                            self._log_replace(template, match_str, replace_expr, pod_expr, new_pod_expr)
        return results

    @staticmethod
    def _log_replace(template, match, replaced_by, old_pod_expr, new_pod_expr):
        """ Log replacements if fingerpointing installed """
        if HAS_FINGERPOINTING:
            from collective.fingerpointing.config import AUDIT_MESSAGE
            from collective.fingerpointing.logger import log_info
            from collective.fingerpointing.utils import get_request_information

            # add logging message to fingerpointing log
            user, ip = get_request_information()
            action = "replace_in_template"
            extras = u"podtemplate={0} match={1} replaced_by={2} old_pod_expr={3} new_pod_expr={4}".format(
                "/".join(template.getPhysicalPath()), match, replaced_by, old_pod_expr, new_pod_expr,
            )
            log_info(unicode(AUDIT_MESSAGE).format(user, ip, action, extras))
