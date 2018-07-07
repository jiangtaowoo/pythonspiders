# -*- coding: utf-8 -*-
import json

class JsonDTO(object):
    """
    parse_data(data, row_path, col_paths)
    """
    _filter_ops = ['not rin', 'not in', 'rin', 'in', '>=', '<=', '!=', '=', '>', '<']

    @staticmethod
    def _stringify_node(node, delimiter='|'):
        if isinstance(node, list):
            return delimiter.join([unicode(x) for x in node])
        elif isinstance(node, dict):
            return delimiter.join([node[k] for k in node])
        elif isinstance(node, str) or isinstance(node, unicode):
            return node.strip()
        else:
            return unicode(node).strip()

    @staticmethod
    def _parse_jpath(jpath):
        segs = [x for x in jpath.split('/') if x]
        return [x for seg in segs for x in seg.split('|')]

    @staticmethod
    def _parse_jpath_segment(jpath_seg):
        """
        [slice ? $@subkey op value]
        [slice ? $ op value]
        [slice]
        [slice@subkey]
        [index@subkey]
        {keyslice ? $@subkey op value}
        {keyslice ? $ op value}
        {key1,key2,key3}
        {~key1,key2,key3}
        {:@subkey}
        return type, slice, filters
        """
        dl_type = 'L' if jpath_seg[0]=='[' else 'D'
        dl_content = [x.strip() for x in jpath_seg[1:-1].split('?')]
        dl_slice = dl_content[0]
        dl_filter = dl_content[1] if len(dl_content)>1 else None
        return dl_type, dl_slice, dl_filter

    @staticmethod
    def _parse_jpath_filter(dl_filter):
        dl_op = None
        for op in JsonDTO._filter_ops:
            if op in dl_filter:
                dl_op = op
                break
        if dl_op:
            dl_filter_content = [x.strip() for x in dl_filter.split(dl_op)]
            dl_selector = dl_filter_content[0]
            ss = [x.strip() for x in dl_selector.split('@')]
            dl_selector = ss[0]
            subkeys = ss[1:] if len(ss)>1 else None
            dl_filter_value = dl_filter_content[1]
            if len(dl_filter_value)>2 and '\\u'==dl_filter_value[:2]:
                dl_filter_value = dl_filter_value.decode('unicode-escape')
            return op, dl_selector, subkeys, dl_filter_value
        else:
            ss = [x.strip() for x in dl_filter.split('@')]
            dl_selector = ss[0]
            subkeys = ss[1:] if len(ss)>1 else None
            return None, dl_selector, subkeys, None

    @staticmethod
    def _parse_jpath_slice(dl_slice):
        """
        [slice]
        [slice@subkey]
        {:}
        {:@subkey}
        """
        contents = [x.strip() for x in dl_slice.split('@')]
        s_slice = contents[0]
        s_subkeys = contents[1:] if len(contents)>1 else None
        return s_slice, s_subkeys

    @staticmethod
    def _perform_slice(data, dl_type, dl_slice):
        """
        1. list
        [0],  [-1], [5]
        [:], [:-5]
        2. dict
        {k1,k2,k3}
        {~k1,k2,k3}
        {:}
        """
        s_slice, s_subkeys = JsonDTO._parse_jpath_slice(dl_slice)
        funcs = {'L':JsonDTO._atom_select_list_data, 'D':JsonDTO._atom_select_dict_data}
        ret_data = funcs[dl_type](data, dl_type, s_slice)
        #对于切片内容, 可以返回下一级的subkey内容
        if s_subkeys:
            if dl_type=='L' and isinstance(ret_data, list):
                for sk in s_subkeys:
                    ret_data = [x[sk] for x in ret_data if sk in x]
            elif dl_type=='D' and isinstance(ret_data, dict):
                for sk in s_subkeys:
                    ret_data = {k:v[sk] for k, v in ret_data.iteritems() if sk in v}
        return ret_data

    @staticmethod
    def _perform_filter(data, dl_type, dl_filter):
        """
        dl_selector is
        $
        $@subkey1
        """
        def _iter_fetch_subkey(item, subkeys):
            xx = item
            if subkeys:
                for sk in subkeys:
                    if sk in xx:
                        xx = xx[sk]
                    else:
                        xx = None
                        break
            return xx
        op, selector, subkeys, value = JsonDTO._parse_jpath_filter(dl_filter)
        res_data = [] if dl_type=='L' else {}
        if dl_type=='L' and isinstance(data, list):
            for x in data:
                xx = _iter_fetch_subkey(x, subkeys)
                if JsonDTO._filter_op_test(op, xx, value):
                    res_data.append(x)
        elif dl_type=='D' and isinstance(data, dict):
            for k in data:
                x = data[k]
                xx = k if selector=='$' and not subkeys else _iter_fetch_subkey(x, subkeys)
                if JsonDTO._filter_op_test(op, xx, value):
                    res_data[k] = x
        return res_data

    @staticmethod
    def _filter_op_test(op, item_val, filter_val):
        if item_val is None:
            return False
        if filter_val:
            if 'in' in op:
                if not isinstance(filter_val, unicode):
                    filter_val = str(filter_val)
                if not isinstance(item_val, unicode):
                    item_val = str(item_val)
                if op == 'not rin':
                    return filter_val not in item_val
                if op == 'not in':
                    return item_val not in filter_val
                elif op == 'rin':
                    return filter_val in item_val
                elif op == 'in':
                    return item_val in filter_val
            elif op == '>=':
                try:
                    return float(item_val) >= float(filter_val)
                except:
                    return item_val >= filter_val
            elif op == '<=':
                try:
                    return float(item_val) <= float(filter_val)
                except:
                    return item_val <= filter_val
            elif op == '!=':
                return item_val != filter_val
            elif op == '=':
                return item_val == filter_val
            elif op == '>':
                try:
                    return float(item_val) > float(filter_val)
                except:
                    return item_val > filter_val
            elif op == '<':
                try:
                    return float(item_val) < float(filter_val)
                except:
                    return item_val < filter_val
        else:   #item value exist or not
            if item_val is not None:
                return True
        return False

    @staticmethod
    def _atom_select_dict_data(data, dl_type, dl_slice):
        if not dl_slice:
            return data
        ret_data = None
        if dl_type == 'D' and isinstance(data, dict):
            if dl_slice[0] == ':':
                return data
            elif dl_slice[0] == '~':
                ret_data = dict()
                exclude_ks = [x.strip() for x in dl_slice[1:].split(',')]
                for k, v in data.iteritems():
                    if k not in exclude_ks:
                        ret_data[k] = v
            else:
                include_ks = [x.strip() for x in dl_slice.split(',')]
                if len(include_ks)>1:
                    ret_data = dict()
                    for k, v in data.iteritems():
                        if k in include_ks:
                            ret_data[k] = v
                else:  #return single value
                    ret_data = data[dl_slice] if dl_slice in data else None
        return ret_data

    @staticmethod
    def _atom_select_list_data(data, dl_type, dl_slice):
        if not dl_slice:
            return data
        ret_data = None
        if dl_type == 'L' and isinstance(data, list):
            if ':' in dl_slice:
                range_info = dl_slice.split(':')
                if len(range_info)==2:
                    start_idx = int(range_info[0]) if range_info[0] else 0
                    end_idx = int(range_info[1]) if range_info[1] else len(data)
                    ret_data = data[start_idx:end_idx]
            else:
                single_idx = int(dl_slice)
                if single_idx>=-len(data) and single_idx<len(data):
                    ret_data = data[single_idx]
        return ret_data

    @staticmethod
    def get_jpath_data(data, jpath):
        segs = JsonDTO._parse_jpath(jpath)
        if not segs:
            return data
        ret_data = data
        for seg in segs:
            dl_type, dl_slice, dl_filter = JsonDTO._parse_jpath_segment(seg)
            ret_data = JsonDTO._perform_slice(ret_data, dl_type, dl_slice)
            if dl_filter:
                ret_data = JsonDTO._perform_filter(ret_data, dl_type, dl_filter)
            if not ret_data:
                return None
        return ret_data

    @staticmethod
    def parse_data(data, row_path, col_paths):
        """
        /[?@salary>8000]|[?@salary!=面议]|[?@age>30]
        """
        #dtocfg = DTOParser.get_dto_config(runner.id)
        #row_jpath = DTOParser.get_row_path(dtocfg)
        #col_jpaths = DTOParser.get_col_paths(dtocfg)
        if not row_path:
            return None
        rows_data = JsonDTO.get_jpath_data(data, row_path)
        if rows_data:
            data_rowset = []
            if isinstance(rows_data, dict):
                rows_data = [rows_data[k] for k in rows_data]
            if isinstance(rows_data, list):
                for raw_row in rows_data:
                    data_row = {}
                    for field_name, col_jpath in col_paths.iteritems():
                        node = JsonDTO.get_jpath_data(raw_row, col_jpath)
                        data_row[field_name] = JsonDTO._stringify_node(node)
                    data_rowset.append(data_row)
            return data_rowset
        else:
            return None

