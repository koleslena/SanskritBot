import unittest
from DictParser import DictParser


class DictParserTestCase(unittest.TestCase):
    def setUp(self):
        self.testfile_jala = open("test_answer_jala.html")
        self.testfile_kR = open("test_answer_kR.html")
        self.html_jala = self.testfile_jala.read()
        self.html_kR = self.testfile_kR.read()

    def tearDown(self):
        self.testfile_jala.close()
        self.testfile_kR.close()

    def test_parser_jala(self):
        parser = DictParser()
        parser.feed(self.html_jala)
        cleaned_res = parser.get_cleaned_answer()
        res = parser.get_answer()
        self.assertEqual(14, len(cleaned_res))
        self.assertEqual('jala', cleaned_res[0])
        self.assertEqual(1219, len(res))

    def test_parser_kR(self):
        parser = DictParser()
        parser.feed(self.html_kR)
        cleaned_res = parser.get_cleaned_answer()
        res = parser.get_answer()
        self.assertEqual(7, len(cleaned_res))
        self.assertEqual('kṛ', cleaned_res[0])
        self.assertEqual(14721, len(res))


if __name__ == '__main__':
    unittest.main()
