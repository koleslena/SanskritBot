from html.parser import HTMLParser


class DictParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.__result = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, link in attrs:
                if name == "href":
                    if link.startswith("http"):
                        self.__result += f"<a href='{link}'>"
                    elif link.startswith("//www"):
                        self.__result += f"<a href='https:{link}'>"

    def handle_data(self, data):
        if self.get_starttag_text() != None and not self.get_starttag_text().startswith("<style"):
            self.__result += data

    def handle_endtag(self, tag):
        if tag == "a":
            self.__result += "</a>"

    def get_cleaned_answer(self):
        lines = self.__result.splitlines()
        return [self.__clean_srt(s) for s in lines if self.__clean_srt(s) != '']

    def __clean_srt(self, str):
        return str.strip().lstrip().rstrip()

    def get_answer(self):
        return self.__result
