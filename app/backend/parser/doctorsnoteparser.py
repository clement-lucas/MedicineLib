# 医師記録 parser class.
# XML 形式の文字列を受け取り、SOAP の内容を抽出する。

from parser.soapparser import SOAPParser as SP

class DoctorsNoteParser(SP):

    def __init__(self, xml):
        super(DoctorsNoteParser, self).__init__(xml, "FREE")

    # SOAP タグか調べて、インデックスを返却する。
    # SOAP タグでない場合は、SOAPParser.IS_NOT_SOAP を返却する。
    def _is_SOAP(self, tag, text):
        if tag == "SUBJECTIVE":
            return self._index_S
        elif tag == "OBJECTIVE":
            return self._index_O
        elif tag == "ASSESSMENT":
            return self._index_A
        elif tag == "PLAN":
            return self._index_P
        else:
            return self.IS_NOT_SOAP
                