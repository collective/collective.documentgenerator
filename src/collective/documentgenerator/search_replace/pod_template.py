from collective.documentgenerator.browser.generation_view import HAS_FINGERPOINTING
from collective.documentgenerator.utils import get_site_root_relative_path
from collective.documentgenerator.utils import temporary_file_name
from plone.namedfile import NamedBlobFile

import collections
import mimetypes
import os
import shutil


SearchReplaceResult = collections.namedtuple(
    "SearchReplaceResult",
    ["pod_expr", "match_start", "match_end", "match", "node_type", "new_pod_expr"],
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
        self.tmp_dir = temporary_file_name(suffix='search_replace')
        self.changed_files = set()

        # compute the (future) file system path of the plone pod templates
        for podtemplate in podtemplates:
            if not podtemplate.odt_file:
                continue  # ignore templates referring another pod template.
            file_extension = podtemplate.odt_file.filename.split(".")[-1].lower()
            template_path = get_site_root_relative_path(podtemplate)
            fs_filename = "{}/{}.{}".format(
                self.tmp_dir, template_path.replace("/", "_"), file_extension
            )
            self.templates_by_filename[fs_filename] = {"obj": podtemplate, "path": template_path}

    def __enter__(self):
        """
        copy the plone pod template content on the file system
        """
        os.mkdir(self.tmp_dir)
        for filename in self.templates_by_filename.keys():
            # clean old files
            if os.path.isfile(filename):
                os.remove(filename)
            # copy the pod templates on the file system.
            with open(filename, "w") as template_file:
                plone_template = self.templates_by_filename[filename]["obj"]
                template_file.write(plone_template.odt_file.data)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # push the result back into the site pod templates
        for filename in self.changed_files:
            with open(filename, "rb") as replaced_file:
                podtemplate = self.templates_by_filename[filename]["obj"]
                result = NamedBlobFile(
                    data=replaced_file.read(),
                    contentType=podtemplate.odt_file.contentType
                    or mimetypes.guess_type(filename)[0],
                    filename=podtemplate.odt_file.filename,
                )
                podtemplate.odt_file = result
        # delete tmp directory
        shutil.rmtree(self.tmp_dir)

    def search(self, find_expr, is_regex=False):
        """
        Search find_expr in self.podtemplates
        :param find_expr: A regex str or simple string
        :param is_regex: use is_regex=False if find_expr is not a regex
        :return: a dict with podtemplate uid as key and list of SearchReplaceResult as value
        """
        from appy.bin.odfgrep import Grep

        grepper = Grep(find_expr, self.tmp_dir, asString=not is_regex, verbose=0)
        grepper.run()
        results = self._prepare_results_output(grepper.matches, is_replacing=False)
        return results

    def replace(self, find_expr, replace_expr, is_regex=False, dry_run=False):
        """
        Replace find_expr match with replace_expr in self.podtemplates
        :param find_expr: A regex str or simple str
        :param replace_expr: A str that will replace find_expr match
        :param is_regex: Use is_regex=False if find_expr is not a regex
        :param dry_run: Perform a dry run and not the actual replacement(s).
        This will not modify the template(s) and can be used safely.
        :return: a dict with podtemplate uid as key and list of SearchReplaceResult as value
        """
        from appy.bin.odfgrep import Grep

        grepper = Grep(
            find_expr,
            self.tmp_dir,
            repl=replace_expr,
            asString=not is_regex,
            dryRun=dry_run,
            verbose=0,
        )
        grepper.run()
        results = self._prepare_results_output(grepper.matches, is_replacing=False)

        for filename in grepper.matches.keys():
            self.changed_files.add(filename)

        return results

    def _prepare_results_output(self, matches, replace_expr="", is_replacing=True):
        """ Prepare results output so we have a nice feedback when searching and replacing """
        results = {}
        for file_path, file_results in matches.items():
            template = self.templates_by_filename[file_path]["obj"]
            template_uid = template.UID()
            results[template_uid] = file_results
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
                "/".join(template.getPhysicalPath()),
                match,
                replaced_by,
                old_pod_expr,
                new_pod_expr,
            )
            log_info(unicode(AUDIT_MESSAGE).format(user, ip, action, extras))
