import unittest
from response_parser import parse, parse_line

class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.line_cases = [
            {
                "key": "jala",
                "text": """<H1><h><key1>jala</key1><key2>jala/</key2><hom>1</hom></h><body><hom>1.</hom> <s>jala/</s>   <lex>mfn.</lex> = <s>jaqa</s> (<ab>cf.</ab> √ <s>jal</s>), stupid (<ab>cf.</ab> <s>°lA<srs/>dkipa</s>, <s>°lA<srs/>Saya</s>), <ls>ŚārṅgP. xxi</ls> (<ab>v.l.</ab>)<info lex="m:f:n"/></body><tail><L>77761</L><pc>414,2</pc></tail></H1>""",
                "answer": """* <b>jala</b> \n mfn.= <i>jaḍa</i> (cf.√ <i>jal</i> ), stupid (cf.<i>°lā</i> dkipa, <i>°lā</i> Saya), ŚārṅgP. xxi(v.l.)""",
            },
            {
                "key": "jal",
                "text": """<H1><h><key1>jal</key1><key2>jal</key2></h><body><s>jal</s><ab>cl.</ab> 1. <s>°lati</s> (<ab>pf.</ab> <s>jajAla</s>, <ls>Pāṇ. viii, 4, 54</ls>, <ab>Sch.</ab>), ‘to be rich’ or ‘to cover’ (derived <ab>fr.</ab> <s>jAla</s>?), <ls>Dhātup. xx, 3</ls>; <div n="to"/>to be sharp, <ls>ib.</ls>; <div n="to"/>to be stiff or dull (for <s>jaq</s>, derived <ab>fr.</ab> <s>jaqa</s>), <ls>ib.</ls> : <ab>cl.</ab> 10.<s>jAlayati</s>, to cover, <ls n="Dhātup.">xxxii, 10</ls>.<info westergaard="jala,20.3,01.0561"/><info verb="root" cp="1,10"/></body><tail><L>77760</L><pc>414,2</pc></tail></H1>""",
                "answer":"""* <b>jal</b> \n <i>jal</i> cl.1. <i>°lati</i> (pf.<i>jajāla</i> , <a href='https://ashtadhyayi.com/sutraani/8/4/54'>Pāṇ. viii, 4, 54</a>, Sch.), ‘to be rich’ or ‘to cover’ (derived fr.<i>jāla</i> ?), Dhātup. xx, 3; to be sharp, ib.; to be stiff or dull (for <i>jaḍ</i> , derived fr.<i>jaḍa</i> ), ib.: cl.10.<i>jālayati</i> , to cover, xxxii, 10.""",
            },
            ]
        self.cases = [
            {
                "case": [{'key': 'jala', 'lnum': 77761, 'data': '<H1><h><key1>jala</key1><key2>jala/</key2><hom>1</hom></h><body><hom>1.</hom> <s>jala/</s>   <lex>mfn.</lex> = <s>jaqa</s> (<ab>cf.</ab> √ <s>jal</s>), stupid (<ab>cf.</ab> <s>°lA<srs/>dkipa</s>, <s>°lA<srs/>Saya</s>), <ls>ŚārṅgP. xxi</ls> (<ab>v.l.</ab>)<info lex="m:f:n"/></body><tail><L>77761</L><pc>414,2</pc></tail></H1>'}, {'key': 'jala', 'lnum': 77762, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body><s>jala/</s>   <lex>m.</lex> (<ab>g.</ab> <s>jvalA<srs/>di</s>) a stupid man, <ls>Śiś. v, 37</ls><info lex="m"/></body><tail><L>77762</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 77763, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body>  <ab>N.</ab> of a man (with the <ab>patr.</ab> <s1 slp1="jAtUkarRya">Jātūkarṇya</s1>), <ls>ŚāṅkhŚr. xvi, 29, 6</ls><info lex="inh"/></body><tail><L>77763</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 77764, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body><s>jala/</s>   <lex>n.</lex> (also <ab>pl.</ab>) water, any fluid, <ls>Naigh. i, 12</ls>; <ls>Yājñ. i, 17</ls>; <ls>MBh.</ls> &amp;c. (<ab>ifc.</ab> <lex type="hwifc">f(<s>A</s>). </lex>)<info lex="f#A:n"/></body><tail><L>77764</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 77765, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body><s>jala/</s>   <lex>n.</lex> a kind of <bot>Andropogon</bot>, <ls>Bhpr. vii, 10, 52</ls> &amp; <ls n="Bhpr. vii, 10,">78</ls>; <ls n="Bhpr. vii,">28, 18</ls><info lex="n"/></body><tail><L>77765</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 77766, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body>  the 4th mansion (in <ab>astrol.</ab>), <ls>VarYogay. iv, 26</ls><info lex="inh"/></body><tail><L>77766</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 77767, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body>  a cow\'s embryo (<s>go-kalaka</s> or <s>°lana</s>), <ls>L.</ls><info lex="inh"/></body><tail><L>77767</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 77768, 'data': '<H1B><h><key1>jala</key1><key2>jala/</key2></h><body>  (= <s>jaqa</s>) frigidity (moral or mental or physical), <ls>W.</ls><info lex="inh"/></body><tail><L>77768</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jalA', 'lnum': 77769, 'data': '<H1B><h><key1>jalA</key1><key2>jalA</key2></h><body><s>jalA</s>   (<s>A</s>), <lex>f.</lex> <ab>N.</ab> of a river, <ls>MBh. iii, 10556.</ls><info lex="f"/></body><tail><L>77769</L><pc>414,2</pc></tail></H1B>'}, {'key': 'jala', 'lnum': 78261, 'data': '<H2><h><key1>jala</key1><key2>jala</key2><hom>2</hom></h><body><hom>2.</hom> <s>jala</s>   <ab>Nom.</ab> <s>°lati</s>, to become water, <ls>Śatr. xiv.</ls><info verb="nom" cp=""/></body><tail><L>78261</L><pc>416,1</pc></tail></H2>'}],
                "answer": [
                    """* <b>jala</b> \n mfn.= <i>jaḍa</i> (cf.√ <i>jal</i> ), stupid (cf.<i>°lā</i> dkipa, <i>°lā</i> Saya), ŚārṅgP. xxi(v.l.)""", 
                    """* <b>jala</b> \n m.(g.<i>jvalā</i> di) a stupid man, Śiś. v, 37""", 
                    """* <b>jala</b> \n N.of a man (with the patr.Jātūkarṇya), ŚāṅkhŚr. xvi, 29, 6""", 
                    """* <b>jala</b> \n n.(also pl.) water, any fluid, Naigh. i, 12; Yājñ. i, 17; MBh.&c. (ifc.f(<i>ā</i> ). )""", 
                    """* <b>jala</b> \n n.a kind of Andropogon, Bhpr. vii, 10, 52& 78; 28, 18""", 
                    """* <b>jala</b> \n the 4th mansion (in astrol.), VarYogay. iv, 26""", 
                    """* <b>jala</b> \n a cow's embryo (<i>go-kalaka</i> or <i>°lana</i> ), L.""", 
                    """* <b>jala</b> \n (= <i>jaḍa</i> ) frigidity (moral or mental or physical), W.""", 
                    """* <b>jalā</b> \n <i>jalā</i> (<i>ā</i> ), f.N.of a river, MBh. iii, 10556.""", 
                    """* <b>jala</b> \n <i>jala</i> Nom.<i>°lati</i> , to become water, Śatr. xiv.""",
                    ],
            }
            ]
    
    def test_parse_answer(self):
        for case in self.line_cases:
            res = parse_line(case["key"], case["text"])
            self.assertEqual(res, case["answer"])
        
        for case in self.cases:
            answer = case["answer"]
            res = parse(case["case"])
            for i in range(len(res)):
                self.assertEqual(res[i], answer[i])


if __name__ == '__main__':
    unittest.main()