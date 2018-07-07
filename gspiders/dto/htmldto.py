# -*- coding: utf-8 -*-
import lxml.html

class HtmlDTO(object):
    """
    node 可能为str, unicode, HtmlElement, 或者包含这些内容的list
    """
    @staticmethod
    def _stringify_node(node, delimiter='|'):
        if not isinstance(node, list):
            if isinstance(node, lxml.html.HtmlElement):
                parts = ([x for x in node.itertext()])
                return ''.join([p for p in parts if p]).strip()
            elif isinstance(node, str) or isinstance(node, unicode):
                return node.strip()
            else:
                return unicode(node).strip()
        else:
            parts = []
            for subnode in node:
                parts.append(HtmlDTO._stringify_node(subnode, delimiter))
            return delimiter.join([p for p in parts if p]).strip()

    @staticmethod
    def parse_data(data, row_path, col_paths):
        # '/D@data/L./D@specification'
        #dtocfg = DTOParser.get_dto_config(runner.id)
        #row_xpath = DTOParser.get_row_path(dtocfg)
        #col_xpaths = DTOParser.get_col_paths(dtocfg)
        if not row_path:
            return None
        datarows = []
        xml_data = lxml.html.fromstring(data)
        row_divs = xml_data.xpath(row_path)
        for div in row_divs:
            data_row = {}
            for field_name, col_xpath in col_paths.iteritems():
                if col_xpath:
                    node = div.xpath(col_xpath)
                    data_row[field_name] = HtmlDTO._stringify_node(node)
            datarows.append(data_row)
        return datarows
