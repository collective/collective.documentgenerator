# -*- coding: utf-8 -*-

import mimetypes
import os
import os.path
import re
import tempfile
import time
import zipfile

import xml.dom.minidom

from collective.documentgenerator.events.styles_events import create_temporary_file
from collective.documentgenerator.utils import remove_tmp_file
from plone.namedfile import NamedBlobFile


class ODTSearchReplace:
    """
    """

    def __init__(self, file_path):
        """
        :param file_path: absolute file path to the ODT file
        """
        self.file_path = file_path

    def search(self, find_expr, ignorecase=False):
        """
        Search find_expr in self.file_path file
        :param find_expr: str -> a regex to find
        :param ignorecase: bool -> ignore text case
        :return:
        """
        with zipfile.ZipFile(self.file_path, "r") as odt_file:
            with odt_file.open("content.xml", "r") as content_xml_file:
                odt_content = content_xml_file.read()
        xml_tree = xml.dom.minidom.parseString(odt_content)
        search_result = self._search_xml_content(xml_tree, find_expr, ignorecase)
        return xml_tree, search_result

    def search_and_replace(self, find_expr, replace_expr=None, ignorecase=False):
        """
        Search for appyPOD code pattern 'find_expr' in the 'annotations' and 'text input' zones
        of odt file 'file_name' Replace the matches by 'replace_expr' Create a new file in folder
        'destination' rather than modify the original file if 'destination' is given
        :param find_expr:
        :param replace_expr:
        :param destination:
        :param ignorecase:
        :return:
        """
        xml_tree, replace_results = self.search(find_expr, ignorecase)

        if len(replace_results) == 0:  # Nothing to replace
            return replace_results

        temp_folder = self._make_temp_folder()
        self._unzip(self.file_path, temp_folder)
        new_content = self._replace_in_xml_tree(xml_tree, replace_results, replace_expr)
        self._overwrite_content_xml(new_content, temp_folder)
        self._zip(temp_folder, self.file_path, odf=True)
        return replace_results

    def _search_xml_content(self, xml_tree, find_expr, ignorecase=False):
        # the two xml tags we want to browse are 'office:annotation' and 'text:text-input',
        # since its the only place where appyPOD code can be written
        annotation_nodes = [
            node.getElementsByTagName("text:p") for node in xml_tree.getElementsByTagName("office:annotation")
        ]

        result = self._search_xml_pod_zone(
            nodes=annotation_nodes, node_type="comment", find_expr=find_expr, ignorecase=ignorecase,
        )

        input_nodes = xml_tree.getElementsByTagName("text:text-input")
        result_inputs = self._search_xml_pod_zone(
            nodes=input_nodes, node_type="input field", find_expr=find_expr, ignorecase=ignorecase,
        )
        result.extend(result_inputs)
        return result

    def _search_xml_pod_zone(self, nodes, node_type, find_expr, ignorecase=False):
        text_lines = []
        node_groups = [self._reach_text_node(node) for node in nodes]
        flags = ignorecase and re.I or 0
        i = 1
        for node_group in node_groups:
            for node in node_group:
                if node.nodeType == node.TEXT_NODE:
                    text = node.data
                    for expr in find_expr:
                        matches = list(re.finditer(expr, text, flags=flags))
                        if matches:
                            text_lines.append(
                                {"matches": matches, "XMLnode": node, "node_number": i, "node_type": node_type}
                            )
            i = i + 1
        return text_lines

    @staticmethod
    def _unzip(source_file, target_folder):
        zip_ref = zipfile.ZipFile(source_file, "r")
        zip_ref.extractall(target_folder)
        zip_ref.close()

    @staticmethod
    def _zip(source_folder, target_file, odf=False):
        """
            Zips the content of p_folder into the zip file whose (preferev(ably)
            absolute filename is p_f. If p_odf is True, p_folder is cev(onsidered
            to contain the standard content of an ODF file (conteev(nt.xml,...).
            In this case, some rules must be respected while bev(uilding the zip
            (see below).
        """
        # Remove p_f if it exists
        if os.path.exists(target_file):
            os.remove(target_file)
        try:
            zipFile = zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED)
        except RuntimeError:
            zipFile = zipfile.ZipFile(target_file, "w")
        # If p_odf is True, insert first the file "ev(etype" (uncompressed), in
        # order to be compliant with the OpenDoev(ument Format specification,
        # section 17.4, that expresses thisev(striction. Else, libraries like
        # "magic", under Linux/Unix, arev(nable to detect the correct mimetype for
        # a pod result (it simplyev( recognizes it as a
        # "application/zip" and not a "application/vndev(.oasis.opendocument.text)"
        if odf:
            mimetypeFile = os.path.join(source_folder, "mimetype")
            # This file may not exist (presumably, ods files from Google Drive)
            if not os.path.exists(mimetypeFile):
                f = file(mimetypeFile, "w")
                f.write(mimetypes[os.path.splitext(f)[-1][1:]])
                f.close()
            zipFile.write(mimetypeFile, "mimetype", zipfile.ZIP_STORED)
        for dir, dirnames, filenames in os.walk(source_folder):
            for name in filenames:
                folderName = dir[len(source_folder) + 1 :]
                # For pev(_odf files, ignore file "mimetype" that was already inserted
                if odf and (folderName == "") and (name == "mimetype"):
                    continue
                zipFile.write(os.path.join(dir, name), os.path.join(folderName, name))
            if not dirnames and not filenames:
                # This is an empty leaf folder. We must create an entry in the
                # zip for him.
                folderName = dir[len(source_folder) :]
                zInfo = zipfile.ZipInfo("%s/" % folderName, time.localtime()[:6])
                zInfo.external_attr = 48
                zipFile.writestr(zInfo, "")
        zipFile.close()

    @staticmethod
    def _make_temp_folder():
        temp_folder_name = "f%f" % time.time()
        temp_folder = os.path.join(tempfile.gettempdir(), temp_folder_name)
        os.mkdir(temp_folder)
        return temp_folder

    @staticmethod
    def _reach_text_node(node):
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

    @staticmethod
    def _overwrite_content_xml(newcontent, tempFolder):
        content_path = os.path.join(tempFolder, "content.xml")
        with open(content_path, "w") as content_file:
            content_file.write(newcontent)

    @staticmethod
    def _replace_in_xml_tree(xml_tree, searchresult, replace_expr):
        for result in searchresult:
            line = result["XMLnode"].data
            result["old_pod_expr"] = line
            replaced = []
            start = 0
            end = 0
            for match in result["matches"]:
                end = match.start()
                replaced.append(line[start:end])
                replaced.append(replace_expr)
                start = match.end()
            replaced.append(line[start:])
            replaced = "".join(replaced)
            result["XMLnode"].data = replaced
        return xml_tree.toxml("utf-8")


class PODTemplateSearchReplace:
    def __init__(self, pod_template):
        self.pod_template = pod_template
        self.dirty = False

    def __enter__(self):
        temp_file = create_temporary_file(self.pod_template.odt_file, "pod_template.odt")
        with open(temp_file.name, "w") as temp_file:
            temp_file.write(self.pod_template.odt_file.data)
        self.temp_file = temp_file
        self.odt_search_replacer = ODTSearchReplace(self.temp_file.name)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.dirty:
            with open(self.temp_file.name, "rb") as binary_file:
                result = NamedBlobFile(
                    data=binary_file.read(),
                    contentType="application/vnd.oasis.opendocument.text",
                    filename=self.pod_template.odt_file.filename,
                )
                self.pod_template.odt_file = result

        remove_tmp_file(self.temp_file.name)

    def search(self, find_expr):
        """
        """
        if type(find_expr) is str or type(find_expr) is unicode:
            find_expr = [find_expr]

        _tree, search_results = self.odt_search_replacer.search(find_expr)

        results = []
        for result in search_results:
            matches = result["matches"]
            pod_expr = result["XMLnode"].data
            for match in matches:
                match_start, match_end = match.start(), match.end()
                results.append(
                    {
                        "pod_expr": pod_expr,
                        "match": pod_expr[match_start:match_end],
                        "match_start": match_start,
                        "match_end": match_end,
                    }
                )
        return results

    def replace(self, find_expr, replace_expr):
        """
        """
        if type(find_expr) is str or type(find_expr) is unicode:
            find_expr = [find_expr]

        replace_results = self.odt_search_replacer.search_and_replace(find_expr, replace_expr)
        if len(replace_results) > 0:
            self.dirty = True
        results = []
        for result in replace_results:
            matches = result["matches"]
            pod_expr = result["XMLnode"].data
            for match in matches:
                match_start, match_end = match.start(), match.end()
                results.append(
                    {
                        "old_pod_expr": result["old_pod_expr"],
                        "new_pod_expr": pod_expr,
                        "match": result["old_pod_expr"][match_start:match_end],
                        "match_start": match_start,
                        "match_end": match_end,
                        "replaced_by": replace_expr,
                    }
                )
        return results
