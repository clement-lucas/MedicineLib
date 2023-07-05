# 看護記録 parser class.
# XML 形式の文字列を受け取り、SOAP の内容を抽出する。

from parser.soapparser import SOAPParser as SP

class NursesNoteParser(SP):

    def __init__(self, xml):
        super(NursesNoteParser, self).__init__(xml, "ARTICLE")

    # SOAP タグか調べて、インデックスを返却する。
    # SOAP タグでない場合は、SOAPParser.IS_NOT_SOAP を返却する。
    def _is_SOAP(self, tag, text):
    # tag が SOAP 且つ text が S の場合
        if tag != "SOAP":
            return self.IS_NOT_SOAP
        
        if text == "S":
            return self._index_S
        elif text == "O":
            return self._index_O
        elif text == "A":
            return self._index_A
        elif text == "P":
            return self._index_P
        else:
            return self.IS_NOT_SOAP
                