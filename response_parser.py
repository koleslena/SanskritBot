from html.parser import HTMLParser
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

Panini_url = "<a href='https://ashtadhyayi.com/sutraani/{}/{}/{}'>{}</a>"

def parse(data):
  lst = []
  for elem in data:
    key = elem['key']
    lst.append(parse_line(key, elem['data']))

  return lst

def parse_line(key, text):
  parser = Parser(key)
  parser.feed(text)

  ans = parser.get_answer()
  #print(ans)
  return f"* <b>{transliterate(key, sanscript.SLP1, sanscript.IAST)}</b> \n {ans}"

def get_arab_num(txt):
    arab_dict = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8}
    lst = txt.split()
    if len(lst) == 2:
        return arab_dict[lst[1].strip().lstrip().rstrip()]
    else:
        return 1

class Parser(HTMLParser):
    def __init__(self, key):
        super().__init__()
        self.reset()
        self.__key = key
        self.__result = ""
        self.__n_middle = False

    def handle_starttag(self, tag, attrs):
        self.__n_middle = True

    def handle_data(self, data):
        if self.get_starttag_text() == "<s>" and self.__n_middle:
            if self.__key + '/' != data:
              text = transliterate(data.rstrip(), sanscript.SLP1, sanscript.IAST)
              self.__result += f"<i>{text}</i> "
        elif data.startswith("Pāṇ."):
            lst = data.split(", ")
            self.__result += Panini_url.format(get_arab_num(lst[0]), lst[1], lst[2], data)
        elif self.get_starttag_text() != None and not self.get_starttag_text().startswith("<key") and self.get_starttag_text() not in ["<L>", "<pc>", "<hom>"]:
            self.__result += data.lstrip()

    def handle_endtag(self, tag):
        self.__n_middle = False

    def get_answer(self):
        return self.__result

