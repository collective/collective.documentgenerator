import os
import mimetypes

from collective.documentgenerator.search_replace.utils import SearchPODTemplateFiles
from collective.documentgenerator.search_replace.utils import SearchAndReplacePODTemplateFiles
from collective.documentgenerator.utils import get_site_root_relative_path
from plone.namedfile import NamedBlobFile


class SearchPODTemplates(SearchPODTemplateFiles):
    """
    Search POD expression among PODTemplates content type
    """

    def __init__(self, pod_templates, find_expr='', ignorecase=False, silent=False):
        """
        :param pod_templates: List of PODTemplate objects
        :param find_expr: A valid regex expression
        :param ignorecase: ignore case while searching
        :param silent: Output change to the
        """
        self.pod_templates = pod_templates
        self.templates_by_filename = {}
        self.tmp_dir = '/tmp/docgen'
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

        # compute the (future) file system path of the plone pod templates
        for pod_template in pod_templates:
            template_path = get_site_root_relative_path(pod_template)
            extension = mimetypes.guess_extension(pod_template.odt_file.contentType)
            fs_filename = '{}/{}{}'.format(self.tmp_dir, template_path.replace('/', '_'), extension)
            self.templates_by_filename[fs_filename] = {'obj': pod_template, 'path': template_path}

        filenames_expr = self.templates_by_filename.keys()

        super(SearchPODTemplates, self).__init__(find_expr, filenames_expr, ignorecase, silent=silent)

    def __enter__(self):
        """
        copy the plone pod template content on the file system
        """
        for filename in self.filenames_expr:
            # clean old files
            if os.path.isfile(filename):
                os.remove(filename)
            # copy the pod templates on the file system.
            template_file = open(filename, 'w')
            plone_template = self.templates_by_filename[filename]['obj']
            template_file.write(plone_template.odt_file.data)
            template_file.close()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for filename in self.filenames_expr:
            if os.path.isfile(filename):
                os.remove(filename)


class SearchAndReplacePODTemplates(SearchPODTemplates, SearchAndReplacePODTemplateFiles):
    """
    Search and replace POD expression among PODTemplates content type
    """

    def __init__(self, pod_templates, find_expr='', replace_expr='', ignorecase=False, silent=False):
        """
        :param pod_templates: List of PODTemplate objects
        :param find_expr: A valid regex expression to find
        :param replace_expr: A string that will replace matched sfind_expr
        :param ignorecase: ignore case while searching
        :param silent: Output change to the
        """
        # templates to effectively replace
        self.replaced_files = set()
        super(SearchAndReplacePODTemplates, self).__init__(pod_templates, find_expr, ignorecase,
                                                           silent=silent)
        super(SearchPODTemplates, self).__init__(find_expr, self.filenames_expr, replace_expr,
                                                 ignorecase, silent=silent)

    def __exit__(self, exc_type, exc_value, traceback):
        # push the result back into the site pod templates
        for filename in self.replaced_files:
            with open(filename, "rb") as replaced_file:
                pod_template = self.templates_by_filename[filename]['obj']
                result = NamedBlobFile(
                    data=replaced_file.read(),
                    contentType=mimetypes.guess_type(filename)[0],
                    filename=pod_template.odt_file.filename,
                )
                pod_template.odt_file = result
        # clean tmp file
        super(SearchAndReplacePODTemplates, self).__exit__(exc_type, exc_value, traceback)

    def replace(self, find_expr, replace_expr, search_results, target_dir):
        new_files = super(SearchPODTemplates, self).replace(find_expr, replace_expr,
                                                            search_results, target_dir)
        # keep track of effectively changed files to push them back into the
        # site
        for new_file in new_files:
            self.replaced_files.add(new_file.filename)
        return new_files
