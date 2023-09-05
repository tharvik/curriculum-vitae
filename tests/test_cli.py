from subprocess import DEVNULL, check_call

import unittest


class CLITestCase(unittest.TestCase):
    def test_gen_empty_odt(self) -> None:
        check_call(["cv", "odt"], stdin=DEVNULL, stdout=DEVNULL)

    def test_gen_empty_pdf(self) -> None:
        for backend in ["libreoffice", "pandoc"]:
            check_call(
                ["cv", "pdf", "--backend", backend], stdin=DEVNULL, stdout=DEVNULL
            )
