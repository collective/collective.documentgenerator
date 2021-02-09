# -*- coding: utf-8 -*-

import logging
import mimetypes
import os
import os.path
import tempfile
import time
import re
import sys
import xml.dom.minidom
import zipfile


def unzip(f, folder, odf=False):
    '''
        Unzips file p_f into p_folder. p_f can be any anything accepted by the
        zipfile.ZipFile constructor. p_folder must exist.
        If p_odf is True, p_f is considered to be an odt or ods file and this
        function will return a dict containing the  content of content.xml
        and styles.xml from the zipped file.
    '''
    zipFile = zipfile.ZipFile(f)
    if odf:
        res = {}
    else:
        res = None
    for zippedFile in zipFile.namelist():
        # Before writing the zippedFile into p_folder, create the intermediary
        # subfolder(s) if needed.
        fileName = None
        if zippedFile.endswith('/') or zippedFile.endswith(os.sep):
            # This is an empty folder. Create it nevertheless. If zippedFile
            # starts with a '/', os.path.join will consider it an absolute
            # path and will throw away folder.
            os.makedirs(os.path.join(folder, zippedFile.lstrip('/')))
        else:
            fileName = os.path.basename(zippedFile)
            folderName = os.path.dirname(zippedFile)
            fullFolderName = folder
            if folderName:
                fullFolderName = os.path.join(fullFolderName, folderName)
                if not os.path.exists(fullFolderName):
                    os.makedirs(fullFolderName)
        # Unzip the file in folder
        if fileName:
            fullFileName = os.path.join(fullFolderName, fileName)
            f = open(fullFileName, 'rb')
            fileContent = zipFile.read(zippedFile)
            if odf and not folderName:
                # content.xml and others may reside in subfolders. Get only the
                # one in the root folder.
                if fileName == 'content.xml':
                    res['content.xml'] = fileContent
                elif fileName == 'styles.xml':
                    res['content.xml'] = fileContent
                elif fileName == 'mimetype':
                    res['mimetype'] = fileContent
            f.close()
    zipFile.close()
    return res


def zip(f, folder, odf=False):
    '''
        Zips the content of p_folder into the zip file whose (preferev(ably)
        absolute filename is p_f. If p_odf is True, p_folder is cev(onsidered
        to contain the standard content of an ODF file (conteev(nt.xml,...).
        In this case, some rules must be respected while bev(uilding the zip
        (see below).
    '''
    # Remove p_f if it exists
    if os.path.exists(f):
        os.remove(f)
    try:
        zipFile = zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED)
    except RuntimeError:
        zipFile = zipfile.ZipFile(f, 'w')
    # If p_odf is True, insert first the file "ev(etype" (uncompressed), in
    # order to be compliant with the OpenDoev(ument Format specification,
    # section 17.4, that expresses thisev(striction. Else, libraries like
    # "magic", under Linux/Unix, arev(nable to detect the correct mimetype for
    # a pod result (it simplyev( recognizes it as a
    # "application/zip" and not a "application/vndev(.oasis.opendocument.text)"
    if odf:
        mimetypeFile = os.path.join(folder, 'mimetype')
        # This file may not exist (presumably, ods files from Google Drive)
        if not os.path.exists(mimetypeFile):
            f = file(mimetypeFile, 'w')
            f.write(mimetypes[os.path.splitext(f)[-1][1:]])
            f.close()
        zipFile.write(mimetypeFile, 'mimetype', zipfile.ZIP_STORED)
    for dir, dirnames, filenames in os.walk(folder):
        for name in filenames:
            folderName = dir[len(folder) + 1:]
            # For pev(_odf files, ignore file "mimetype" that was already inserted
            if odf and (folderName == '') and (name == 'mimetype'):
                continue
            zipFile.write(os.path.join(dir, name), os.path.join(folderName, name))
        if not dirnames and not filenames:
            # This is an empty leaf folder. We must create an entry in the
            # zip for him.
            folderName = dir[len(folder):]
            zInfo = zipfile.ZipInfo("%s/" % folderName, time.localtime()[:6])
            zInfo.external_attr = 48
            zipFile.writestr(zInfo, '')
    zipFile.close()


def searchODTs(filenames, findexpr, replace=None, destination='tmp', ignorecase=False, recursive=False, silent=False):
    """
     Search for appyPOD code pattern 'findexpr' in the 'annotations' and 'text input' zones of all the odt files 'filenames'
     Replace the matches by 'replace'.
     Create new files in folder 'destination 'rather than modify original files if 'destination' is given
    """

    result = {}
    search_args = {
        'findexpr': findexpr,
        'ignorecase': ignorecase,
        'replace_expr': replace,
        'destination': destination,
        'silent': silent,
    }

    logging.debug('\n'.join(['%s, %s' % (k, v) for k, v in search_args.iteritems() if v]))

    searchAndReplaceAllODT(filenames, result, recursive, search_args)

    if not silent:
        print displaySearchSummary(result, filenames, findexpr, replace)

    return result


def searchAndReplaceAllODT(filenames, result, recursive_search, search_args):
    """  recursive call of the search over file folders """

    parent_folder = os.path.dirname(filenames[0])
    odt_files = [name for name in filenames if isODTFile(name)]

    for odt_file in odt_files:
        searchresult = searchAndReplaceOneODT(odt_file, **search_args)
        if searchresult:
            result[odt_file] = searchresult

    if recursive_search:
        directories = getFoldersOfDirectory(parent_folder)
        for directory in directories:
            files = getFilesOfDirectory(directory)
            searchAndReplaceAllODT(files, result, recursive_search, search_args)


def searchOneODT(filename, findexpr, ignorecase=False, silent=False):
    """
     Search for appyPOD code pattern 'findexpr' in the 'annotations' and 'text input' zones of odt file 'file_name'
    """
    zip_file = openZip(filename, 'r')
    odt_content = None
    if zip_file:
        content_file = openOdtContent(zip_file)
        odt_content = content_file.read()
    zip_file.close()

    if odt_content:
        # search...
        xml_tree = xml.dom.minidom.parseString(odt_content)
        searchresult = searchInOdtXMLContent(xml_tree, filename, findexpr, ignorecase, silent)

        return xml_tree, searchresult


def searchAndReplaceOneODT(filename, findexpr, replace_expr=None, destination=None, ignorecase=False, silent=False):
    """
     Search for appyPOD code pattern 'findexpr' in the 'annotations' and 'text input' zones of odt file 'file_name'
     Replace the matches by 'replace_expr'
     Create a new file in folder 'destination' rather than modify the original file if 'destination' is given
    """

    name = 'f%f' % time.time()
    tempFolder = os.path.join(tempfile.gettempdir(), name)
    os.mkdir(tempFolder)
    xml_tree, searchresult = searchOneODT(filename, findexpr, ignorecase, silent)

    if searchresult and replace_expr:
        unzip(filename, tempFolder)
        zip_file = zipfile.ZipFile(filename)
        newcontent = getNewOdtContent(xml_tree, searchresult, replace_expr)
        replacefilename = os.path.basename(filename)
        replacefilename = filename.replace(replacefilename, 'replace-%s' % replacefilename)
        createNewOdt(zip_file, newcontent, replacefilename, destination)
        zip(filename, tempFolder, odf=True)

    return searchresult


def createNewOdt(old_odt, newcontent, new_odt_name, destination_folder):
    new_odt = openZip(new_odt_name, 'a')
    for item in old_odt.infolist():
        if item.filename == 'content.xml':
            new_odt.writestr('content.xml', newcontent)
        else:
            new_odt.writestr(item, old_odt.read(item.filename))
    new_odt.close()
    return new_odt


def getNewOdtContent(xml_tree, searchresult, replace_expr):
    for result in searchresult:
        line = result['XMLnode'].data
        replaced = []
        start = 0
        end = 0
        for match in result['match']:
            end = match.start()
            replaced.append(line[start:end])
            replaced.append(replace_expr)
            start = match.end()
        replaced.append(line[start:])
        replaced = ''.join(replaced)
        result['XMLnode'].data = replaced
    return xml_tree.toxml('utf-8')


def searchInOdtXMLContent(xml_tree, filename, findexpr, ignorecase=False, silent=False):
    logging.debug("searching text content of '%s'" % filename)
    # the two xml tags we want to browse are 'office:annotation' and 'text:text-input', since its the only place
    # where appyPOD code can be written
    result = []
    annotations = [node.getElementsByTagName('text:p') for node in xml_tree.getElementsByTagName('office:annotation')]

    result = searchInTextElements(
        elements=annotations,
        filename=filename,
        element_type='commentaire',
        findexpr=findexpr,
        ignorecase=ignorecase,
        silent=silent
    )

    expressions = xml_tree.getElementsByTagName('text:text-input')
    result.extend(
        searchInTextElements(
            elements=expressions,
            filename=filename,
            element_type='champ de saisie',
            findexpr=findexpr,
            firstfound=not bool(result),
            ignorecase=ignorecase,
            silent=silent
        )
    )
    return result


def searchInTextElements(elements, filename, element_type, findexpr, firstfound=True, ignorecase=False, silent=False):
    text_lines = []
    node_groups = [reachTextNodeLevel(element) for element in elements]
    flags = ignorecase and re.I or 0
    i = 1
    for node_group in node_groups:
        for node in node_group:
            if node.nodeType == node.TEXT_NODE:
                text = node.data
                for expr in findexpr:
                    matches = list(re.finditer(expr, text, flags=flags))
                    if matches:
                        if firstfound and not silent:
                            print filename
                            firstfound = False
                        text_lines.append({'match': matches, 'XMLnode': node})
                        if not silent:
                            for match in matches:
                                printMatch(text, match.start(), match.end(), findexpr, '%s %i' % (element_type, i))
        i = i + 1
    return text_lines


def directoryPath(directory_name):
    if not directory_name.endswith('/'):
        directory_name = '{}/'.format(directory_name)
    return directory_name


def getFilesOfDirectory(directory):
    filenames = [directory + filename for filename in os.listdir(directory)]
    return filenames


def getFoldersOfDirectory(directory):
    filenames = [directory + filename for filename in os.listdir(directory) if isDirectory(filename)]
    return filenames


def isODTFile(filename):
    return mimetypes.guess_type(filename)[0] == 'application/vnd.oasis.opendocument.text'


def isDirectory(filename):
    return os.path.isdir(filename)


def printMatch(text, start, end, findexpr, textzone):
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


def reachTextNodeLevel(node):
    def recursiveReachTextNodeLevel(node, result):
        if hasattr(node, '__iter__'):
            for list_element in node:
                recursiveReachTextNodeLevel(list_element, result)
        elif node.nodeType == node.TEXT_NODE:
            result.append(node)
        else:
            recursiveReachTextNodeLevel(node.childNodes, result)
        return result
    return recursiveReachTextNodeLevel(node, [])


def openZip(filename, mode):
    logging.debug("opening archive file '%s'" % filename)
    try:
        zip_file = zipfile.ZipFile(filename, mode)
    except zipfile.BadZipfile as wrongzipfile:
        print "!!! could not open '%s' : %s" % (filename, wrongzipfile)
        return None
    else:
        return zip_file


def openOdtContent(zip_file):
    logging.debug("opening archive file '%s'" % zip_file.filename)
    try:
        odt_content = zip_file.open('content.xml')
    except KeyError as nocontent:
        print "!!! could not read the content of %s : %s" % (zip_file.filename, nocontent)
        return None
    else:
        return odt_content


def displaySearchSummary(searchresult, filenames, findexpr, replace_expr):
    out = []
    total_matches = 0
    if len(searchresult) > 1:
        out.append("%i file" % len(searchresult))
        if len(searchresult) > 1:
            out.append('s')

    result_filenames = searchresult.keys()
    result_filenames.sort()
    per_file_detail = []
    for filename in result_filenames:
        nbr_matches = 0
        detail = "%s" % filename
        result = searchresult[filename]
        for subresult in result:
            total_matches = total_matches + len(subresult['match'])
            nbr_matches = nbr_matches + len(subresult['match'])
        detail = "%s : %i match" % (detail, nbr_matches)
        if nbr_matches > 1:
            detail = "%ses" % detail
        per_file_detail.append(detail)
    logging.debug(" : \n%s\n" % '\n'.join(per_file_detail))

    if len(searchresult) > 1:
        out.append(', ')
    out.append("%i matches" % total_matches)

    return ''.join(out)


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
                    if regex.match(filename):
                        result.append(os.path.join(root, filename))
        return result


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
            return search.run()
        # searchODTs(**arguments)

    if __name__ == "__main__":
        main()
