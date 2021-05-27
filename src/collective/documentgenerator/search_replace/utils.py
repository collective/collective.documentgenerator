# -*- coding: utf-8 -*-

import datetime
import logging
import mimetypes
import os
import os.path
import re
import shutil
import sys
import xml.dom.minidom
import zipfile


CONTENT_XML = "content.xml"
STYLES_XML = "styles.xml"


class SearchPODTemplateFiles(object):
    """
    """

    def __init__(self, find_expr, filenames_expr, ignorecase=False, recursive=False, silent=False):
        """
        """
        self.flags = ignorecase and re.I or 0
        find_expr = type(find_expr) in (list, tuple) and find_expr[0] or find_expr
        self.find_expr = re.compile(find_expr, self.flags)
        self.filenames_expr = filenames_expr
        self.ignorecase = ignorecase
        self.recursive = recursive
        self.silent = silent
        self.SEARCHABLE_FILES = (CONTENT_XML, STYLES_XML)

    def run(self, find_expr=None):  # pragma: no cover
        """
        """
        # we can run the search again with a new find_expr
        self.find_expr = find_expr and re.compile(find_expr, self.flags) or self.find_expr

        files = self.find_files(self.filenames_expr, self.recursive)
        search_result = self.search(self.find_expr, files)
        return search_result

    def find_files(self, filenames_expr, recursive=False):  # pragma: no cover
        """
        """
        result = []
        base_paths = list(set([os.path.dirname(path) or "." for path in filenames_expr]))
        files_exprs = [os.path.split(n)[1] for n in filenames_expr]
        regexs = [re.compile(expr) for expr in files_exprs]

        for base_path in base_paths:
            if recursive:
                for root, dirs, filenames in os.walk(base_path):
                    for filename in filenames:
                        for regex in regexs:
                            if regex.match(filename) and self.is_ODF_file(filename):
                                result.append(os.path.join(root, filename))
            else:
                for filename in os.listdir(base_path):
                    for regex in regexs:
                        if regex.match(filename) and self.is_ODF_file(filename):
                            result.append(os.path.join(base_path, filename))
        return list(set(result))

    def is_ODF_file(self, filename):  # pragma: no cover
        guess = mimetypes.guess_type(filename)[0]
        is_ODF = guess and guess.startswith("application/vnd.oasis.opendocument")
        return is_ODF

    def search(self, find_expr, files_paths):
        """
        """
        result = {}
        for filename in files_paths:
            for SEARCHABLE_FILE in self.SEARCHABLE_FILES:
                file_content = self.open_template_content(filename, SEARCHABLE_FILE)
                if not file_content:
                    continue
                # search...
                xml_tree = xml.dom.minidom.parseString(file_content)
                search_result = self.search_XML_content(xml_tree, find_expr)
                if search_result:
                    if not result.get(filename):
                        result[filename] = {}
                    result[filename][SEARCHABLE_FILE] = (xml_tree, search_result)
                    if not self.silent:
                        display = self.get_result_display(search_result)
                        print(filename)
                        print("\n".join(display))
        return result

    def open_zip(self, filename, mode):
        logging.debug("opening archive file '%s'" % filename)
        try:
            zip_file = zipfile.ZipFile(filename, mode)
        except zipfile.BadZipfile as wrongzipfile:
            print("!!! could not open '%s' : %s" % (filename, wrongzipfile))
            return None
        else:
            return zip_file

    def open_template_content(self, template_file, file):
        zip_file = self.open_zip(template_file, "r")
        logging.debug("opening archive file '%s'" % zip_file.filename)
        try:
            odf_file = zip_file.open(file)
            odf_content = odf_file.read()
            return odf_content
        except KeyError as nocontent:
            print("!!! could not read the content of %s : %s" % (zip_file.filename, nocontent))
            return None
        finally:
            zip_file.close()

    def search_XML_content(self, xml_tree, findexpr):
        # the two xml tags we want to browse are 'office:annotation' and 'text:text-input', since its the only place
        # where appyPOD code can be written
        annotation_nodes = [
            node.getElementsByTagName("text:p") for node in xml_tree.getElementsByTagName("office:annotation")
        ]
        result = []
        result.extend(self.search_XML_pod_zone(annotation_nodes, "comment", findexpr))

        input_nodes = xml_tree.getElementsByTagName("text:text-input")
        result.extend(self.search_XML_pod_zone(input_nodes, "input field", findexpr))
        return result

    def search_XML_pod_zone(self, nodes, node_type, findexpr):
        text_lines = []
        node_groups = [self.reach_text_node(node) for node in nodes]
        i = 1
        for node_group in node_groups:
            for node in node_group:
                text = node.data
                matches = list(findexpr.finditer(text))
                if matches:
                    text_lines.append(
                        {"matches": matches, "XMLnode": node, "node_number": i, "node_type": node_type}
                    )
            i = i + 1
        return text_lines

    def reach_text_node(self, node):
        def recursive_reach_text_node(node, result):
            if hasattr(node, "__iter__"):
                for list_node in node:
                    recursive_reach_text_node(list_node, result)
            elif node.nodeType == node.TEXT_NODE:
                result.append(node)
            else:
                recursive_reach_text_node(node.childNodes, result)
            return result

        return recursive_reach_text_node(node, [])

    def get_result_display(self, searchresult):  # pragma: no cover
        to_display = []
        for result in searchresult:
            text = result["XMLnode"].data
            textzone = "%s %i" % (result["node_type"], result["node_number"])
            for match in result["matches"]:
                start = match.start()
                end = match.end()
                display_line = ["", "", ""]
                d_start = 0
                if start > 100:
                    d_start = start - 100
                    display_line[0] = "..."
                d_end = len(text)
                if end + 100 < len(text):
                    d_end = end + 100
                    display_line[2] = "..."
                if sys.stdout.isatty():
                    text_display = "%s\033[93m%s\033[0m%s" % (
                        text[d_start:start],
                        text[start:end],
                        text[end:d_end],
                    )
                else:
                    text_display = text[d_start:d_end]
                display_line[1] = text_display
                final_display_line = "".join(display_line)
                if display_line[0] or display_line[2]:
                    display = "  %s : %s > %s" % (textzone, text_display, final_display_line)
                else:
                    display = "  %s : %s" % (textzone, text_display)
                to_display.append(display)
        return to_display


class SearchAndReplacePODTemplateFiles(SearchPODTemplateFiles):
    """
    """

    def __init__(
        self,
        find_expr,
        filenames_expr,
        replace,
        target_dir=None,
        ignorecase=False,
        recursive=False,
        silent=True,
        backup=True,
    ):
        """
        """
        super(SearchAndReplacePODTemplateFiles, self).__init__(
            find_expr, filenames_expr, ignorecase, recursive, silent
        )
        self.replace_expr = replace
        self.target_dir = target_dir
        self.tmp_dir = "/tmp/docgen"
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)
        if backup:
            self.backup_dir = os.path.join(self.tmp_dir, "{}-backup".format(str(datetime.datetime.today())))
            os.mkdir(self.backup_dir)

    def run(self, find_expr="", replace_expr=""):  # pragma: no cover
        """
        """
        # we can run the replace again with a new find_expr and a new replace_expr
        self.find_expr = find_expr and re.compile(find_expr, self.flags) or self.find_expr
        self.replace_expr = replace_expr and replace_expr or self.replace_expr

        search_result = super(SearchAndReplacePODTemplateFiles, self).run()
        new_files = self.replace(self.find_expr, self.replace_expr, search_result, self.target_dir)
        return search_result, new_files

    def replace(self, find_expr, replace_expr, search_results, target_dir):
        """
        """
        new_files = []
        for filename, search_result in search_results.iteritems():
            zip_file = zipfile.ZipFile(filename)
            backup_filename = os.path.split(filename)[-1]
            new_contents = {}
            if self.recursive:
                backup_filename = filename.strip("./").replace("/", "-")
            if hasattr(self, "backup_dir"):
                shutil.copyfile(filename, "{}/{}".format(self.backup_dir, backup_filename))
            for sub_file, sub_file_search_result in search_result.items():
                xml_tree, match_result = sub_file_search_result
                new_contents[sub_file] = self.get_ODF_new_content(xml_tree, match_result, replace_expr)

            new_filename = target_dir and os.path.join(target_dir, backup_filename) or filename
            new_files.append(self.create_new_ODF(zip_file, new_contents, new_filename, target_dir))
        return new_files

    def create_new_ODF(self, old_odf, newcontents, new_odf_name, target_dir):
        in_place = False
        new_tmp_odf_name = new_odf_name
        if old_odf.filename == new_odf_name:
            new_tmp_odf_name = "{}.tmp".format(new_odf_name)
            in_place = True

        new_odf = self.open_zip(new_tmp_odf_name, "a")
        for item in old_odf.infolist():
            if item.filename in newcontents.keys():
                new_odf.writestr(item.filename, newcontents[item.filename], zipfile.ZIP_DEFLATED)
            else:
                new_odf.writestr(item, old_odf.read(item.filename))
        old_odf.close()
        new_odf.close()

        if in_place:
            os.remove(old_odf.filename)
            shutil.move(new_tmp_odf_name, old_odf.filename)
            new_odf = self.open_zip(new_odf_name, "r")
            new_odf.close()

        return new_odf

    def get_ODF_new_content(self, xml_tree, match_result, replace_expr):
        for result in match_result:
            line = result["XMLnode"].data
            replaced = self.find_expr.sub(replace_expr, line)
            result["XMLnode"].data = replaced
        return xml_tree.toxml("utf-8")


# parsing arguments code
req_version = (2, 7)
cur_version = sys.version_info

if cur_version >= req_version:  # pragma: no cover
    import argparse

    def parseArguments():
        parser = argparse.ArgumentParser(
            description="Search and replace in comments and input fields of .odf files"
        )
        parser.add_argument("find_expr", action="append")
        parser.add_argument("--replace")
        parser.add_argument("-d", "--target_dir")
        parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
        parser.add_argument("-i", "--ignorecase", action="store_true")
        parser.add_argument("-r", "--recursive", action="store_true")
        parser.add_argument("-s", "--silent", action="store_true", default=False)
        parser.add_argument("-E", "--extended-regexp", action="store_true", default=False)
        parser.add_argument("filenames_expr", nargs="*", default=".")
        return parser.parse_args()

    def main():
        arguments = parseArguments()
        verbosity = arguments.__dict__.pop("verbose")
        if verbosity:
            logging.basicConfig(level=logging.DEBUG)
        arguments = vars(arguments)

        is_regex = arguments.pop("extended_regexp")
        if not is_regex:
            arguments["find_expr"] = [re.escape(expr) for expr in arguments["find_expr"]]

        if not arguments["replace"]:
            search = SearchPODTemplateFiles(**dict([(k, v) for k, v in arguments.iteritems() if v]))
            result = search.run()
        else:
            replace = SearchAndReplacePODTemplateFiles(**dict([(k, v) for k, v in arguments.iteritems() if v]))
            result = replace.run()
        return result

    if __name__ == "__main__":
        main()
