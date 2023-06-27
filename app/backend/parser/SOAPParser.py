# SOAP parser class.
# XML 形式の文字列を受け取り、SOAP の内容を抽出する。

import xml.etree.ElementTree as ET

class SOAPParser:

    # プロパティ S
    @property
    def S(self):
        return self._soap[self._index_S]
    
    # プロパティ O
    @property
    def O(self):
        return self._soap[self._index_O]
    
    # プロパティ A
    @property
    def A(self):
        return self._soap[self._index_A]
    
    # プロパティ P
    @property
    def P(self):
        return self._soap[self._index_P]

    # SOAP タグではなかった
    IS_NOT_SOAP = -2
        
    def __init__(self, xml, content_tag):
        self.xml = xml
        self._content_tag = content_tag
        self.root = ET.fromstring(self.xml)
        self._soap = ["","","",""]
        self._index_nodata = -1
        self._index_S = 0
        self._index_O = 1
        self._index_A = 2
        self._index_P = 3
        self._parse()

    def _parse(self):
        is_content = False
        _now_soap_index = self._index_nodata
        for elem in self.root.iter():
            # content タグを見つけた。
            if elem.tag == self._content_tag:
                is_content = True
                if _now_soap_index == self._index_nodata:
                    # SOAP が見つかっていない場合は、無視する。
                    continue
                else:
                    # self._soap[_now_soap_index] の文字列長が1以上であれば、改行を追加する。
                    if len(self._soap[_now_soap_index]) > 0:
                        self._soap[_now_soap_index] += "\n"
                    
                    # SOAP が見つかっている場合は、SOAP に追加する。
                    self._soap[_now_soap_index] += elem.text

            # FREE タグ取得中に他のタグを見つけた。
            elif is_content:
                _now_soap_index = self._index_nodata
                is_content = False

            # SOAP タグか調べて、 IS_NOT_SOAP 以外の場合は、インデックスを設定する。
            idx = self._is_SOAP(elem.tag, elem.text)
            if idx != self.IS_NOT_SOAP:
                _now_soap_index = idx
           
    
    # SOAP タグか調べて、インデックスを返却する。
    # SOAP タグでない場合は、SOAPParser.IS_NOT_SOAP を返却する。
    def _is_SOAP(self, tag, text):
        return self.IS_NOT_SOAP
                