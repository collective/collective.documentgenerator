# -*- coding: utf-8 -*-

import logging
import mimetypes
import os
import os.path
import re
import sys
import xml.dom.minidom
import zipfile


class Search():
    """
    """

    def __init__(self, find_expr, filenames_expr, ignorecase=False, recursive=False):
        """
        """
        self.find_expr = find_expr
        self.filenames_expr = filenames_expr
        self.ignorecase = ignorecase
        self.recursive = recursive
        self.silent = False

    def run(self):
        """
        """
        files = self.find_files(self.filenames_expr, self.recursive)
        search_result = self.search(self.find_expr, files, self.ignorecase)
        return search_result

    def find_files(self, filenames_expr, recursive=False):
        """
        """
        result = []
        base_path = os.path.dirname(filenames_expr[0])
        files_exprs = [os.path.split(n)[1] for n in filenames_expr]

        regexs = [re.compile(expr) for expr in files_exprs]

        for root, dirs, filenames in os.walk(base_path):
            for filename in filenames:
                for regex in regexs:
                    if regex.match(filename) and self.is_ODT_file(filename):
                        result.append(os.path.join(root, filename))
        return list(set(result))

    def is_ODT_file(self, filename):
        return mimetypes.guess_type(filename)[0].startswith('application/vnd.oasis.opendocument')

    def search(self, find_expr, files_paths, ignorecase=False):
        """
        """
        result = {}
        for filename in files_paths:
            zip_file = self.openZip(filename, 'r')
            odt_content = None
            if zip_file:
                content_file = self.openOdtContent(zip_file)
                odt_content = content_file.read()
                zip_file.close()

            if odt_content:
                # search...
                xml_tree = xml.dom.minidom.parseString(odt_content)
                search_result = self.search_XML_content(xml_tree, filename, find_expr, ignorecase)
                if search_result:
                    result[filename] = (xml_tree, search_result)
                    self.print_match(find_expr, filename, search_result)
        return result

    def openZip(self, filename, mode):
        logging.debug("opening archive file '%s'" % filename)
        try:
            zip_file = zipfile.ZipFile(filename, mode)
        except zipfile.BadZipfile as wrongzipfile:
            print "!!! could not open '%s' : %s" % (filename, wrongzipfile)
            return None
        else:
            return zip_file

    def openOdtContent(self, zip_file):
        logging.debug("opening archive file '%s'" % zip_file.filename)
        try:
            odt_content = zip_file.open('content.xml')
        except KeyError as nocontent:
            print "!!! could not read the content of %s : %s" % (zip_file.filename, nocontent)
            return None
        else:
            return odt_content

    def search_XML_content(self, xml_tree, filename, findexpr, ignorecase=False):
        logging.debug("searching text content of '%s'" % filename)
        # the two xml tags we want to browse are 'office:annotation' and 'text:text-input', since its the only place
        # where appyPOD code can be written
        annotation_nodes = [node.getElementsByTagName('text:p') for node in
                            xml_tree.getElementsByTagName('office:annotation')]

        result = self.search_XML_pod_zone(
            nodes=annotation_nodes,
            filename=filename,
            node_type='commentaire',
            findexpr=findexpr,
            ignorecase=ignorecase,
        )

        input_nodes = xml_tree.getElementsByTagName('text:text-input')
        result_inputs = self.search_XML_pod_zone(
            nodes=input_nodes,
            filename=filename,
            node_type='champ de saisie',
            findexpr=findexpr,
            ignorecase=ignorecase,
        )
        result.extend(result_inputs)
        return result

    def search_XML_pod_zone(self, nodes, filename, node_type, findexpr, ignorecase=False):
        text_lines = []
        node_groups = [self.reach_text_node(node) for node in nodes]
        flags = ignorecase and re.I or 0
        i = 1
        for node_group in node_groups:
            for node in node_group:
                if node.nodeType == node.TEXT_NODE:
                    text = node.data
                    for expr in findexpr:
                        matches = list(re.finditer(expr, text, flags=flags))
                        if matches:
                            text_lines.append(
                                {
                                    'matches': matches,
                                    'XMLnode': node,
                                    'node_number': i,
                                    'node_type': node_type
                                }
                            )
            i = i + 1
        return text_lines

    def reach_text_node(self, node):
        def recursive_reach_text_node(node, result):
            if hasattr(node, '__iter__'):
                for list_node in node:
                    recursive_reach_text_node(list_node, result)
            elif node.nodeType == node.TEXT_NODE:
                result.append(node)
            else:
                recursive_reach_text_node(node.childNodes, result)
            return result
        return recursive_reach_text_node(node, [])

    def print_match(self, findexpr, filename, searchresult):
        print filename
        for result in searchresult:
            text = result['XMLnode'].data
            textzone = '%s %i' % (result['node_type'], result['node_number'])
            for match in result['matches']:
                start = match.start()
                end = match.end()
                display_line = ['', '', '']
                d_start = 0
                if start > 100:
                    d_start = start - 100
                    display_line[0] = '...'
                d_end = len(text)
                if end + 100 < len(text):
                    d_end = end + 100
                    display_line[2] = '...'
                if sys.stdout.isatty():
                    text = '%s\033[93m%s\033[0m%s' % (text[d_start:start], text[start:end], text[end:d_end])
                else:
                    text = text[d_start:d_end]
                display_line[1] = text
                display_line = ''.join(display_line)
                if len(findexpr) > 1:
                    print "  %s : %s > %s" % (textzone, text, display_line)
                else:
                    print "  %s : %s" % (textzone, display_line)


class SearchAndReplace(Search):
    """
    """

    def __init__(self, find_expr, filenames_expr, replace_expr, tmpdir=None, ignorecase=False, recursive=False):
        """
        """
        super(SearchAndReplace, self).__init__(find_expr, filenames_expr, ignorecase, recursive)
        self.replace_expr = replace_expr
        self.tmpdir = tmpdir

    def run(self):
        """
        """
        files = self.find_files(self.filenames_expr, self.recursive)
        search_result = self.searchAndReplaceAllODT(self.find_expr, self.replace_expr, files, self.ignorecase, self.tmpdir)
        return search_result


# parsing arguments code
req_version = (2, 7)
cur_version = sys.version_info

if cur_version >= req_version:
    import argparse

    def parseArguments():
        parser = argparse.ArgumentParser(description='Search and replace in comments and input fields of .odt files')
        parser.add_argument('find_expr', action='append')
        parser.add_argument('--replace')
        parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
        parser.add_argument('-i', '--ignorecase', action='store_true')
        parser.add_argument('-r', '--recursive', action='store_true')
        parser.add_argument('filenames_expr', nargs='+')
        return parser.parse_args()

    def main():
        arguments = parseArguments()
        verbosity = arguments.__dict__.pop('verbose')
        if verbosity:
            logging.basicConfig(level=logging.DEBUG)
        arguments = vars(arguments)
        if not arguments['replace']:
            search = Search(**dict([(k, v) for k, v in arguments.iteritems() if v]))
            result = search.run()
            return result

    if __name__ == "__main__":
        main()
