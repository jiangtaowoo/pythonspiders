# -*- coding: utf-8 -*-
import lxml.html
from basedto import BaseDTO

class HtmlDTO(BaseDTO):
    def _stringify_node(node):
        parts = ([x for x in node.itertext()])
        return ''.join(filter(None, parts)).strip()

    def parse_data(self, sitename, data, dmaps):
        # '/D@data/L./D@specification'
        sitedto = self._get_sitedto_from_sitename(sitename)
        row_xpath = sitedto['row_def']['path']
        col_xpaths = sitedto['col_def']
        xml_data = lxml.html.fromstring(data)
        row_divs = xml_data.xpath(row_xpath)
        data_rowset = []
        for div in row_divs:
            data_row = {}
            for field_name, col_xpath in col_xpaths.iteritems():
                if col_xpath:
                    retnode = div.xpath(col_xpath)
                    if isinstance(retnode, lxml.html.HtmlElement):
                        data_row[field_name] = self._stringify_node(retnode)
                    elif isinstance(retnode, list):
                        data_row[field_name] = retnode[0]
                    else:
                        data_row[field_name] = str(retnode)
            data_rowset.append(data_row)
        return data_rowset