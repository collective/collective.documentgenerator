from collective import documentgenerator

import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestNamespace(unittest.TestCase):
    def test_pep420_sibling_not_hidden(self):
        """A PEP 420 portion of the namespace imports when this package comes first on sys.path."""
        src = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(documentgenerator.__file__))))
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        os.mkdir(os.path.join(tmp, "collective"))
        open(os.path.join(tmp, "collective", "pep420_sibling.py"), "w").close()
        code = "import sys; sys.path[:0] = [%r, %r]; import collective.pep420_sibling" % (src, tmp)
        subprocess.check_call([sys.executable, "-S", "-c", code])
