# -*- coding: utf-8 -*-
from basedto import BaseDTO

class JsonDTO(BaseDTO):
    def __init__(self):
        BaseDTO.__init__(self)
        self.filter_ops = [' not rin ', ' not in ', ' rin ', ' in ', '>=', '<=', '!=', '=', '>', '<']

    def _parse_jpath(self, jpath_segment):
        dl_type = jpath_segment[0]
        dl_ind = jpath_segment[1:]
        if len(dl_ind)>1 and dl_ind[0]=='[' and dl_ind[-1]==']':
            dl_selector = dl_ind[1:-1]
            if len(dl_selector)>0:
                return dl_type, dl_selector
        return None, None

    def _parse_filter_op(self, dl_filter_jpath):
        for op in self.filter_ops:
            if op in dl_filter_jpath:
                return op
        return None

    def _filter_op_test(self, op, item_val, filter_val):
        if not item_val:
            return False
        if filter_val:
            if 'in' in op:
                if not isinstance(filter_val, unicode):
                    filter_val = str(filter_val)
                if not isinstance(item_val, unicode):
                    item_val = str(item_val)
                if op == ' not rin ':
                    return filter_val not in item_val
                if op == ' not in ':
                    return item_val not in filter_val
                elif op == ' rin ':
                    return filter_val in item_val
                elif op == ' in ':
                    return item_val in filter_val
            elif op == '>=':
                return float(item_val) >= float(filter_val)
            elif op == '<=':
                return float(item_val) <= float(filter_val)
            elif op == '!=':
                return item_val != filter_val
            elif op == '=':
                return item_val == filter_val
            elif op == '>':
                return float(item_val) > float(filter_val)
            elif op == '<':
                return float(item_val) < float(filter_val)
        else:
            if item_val:
                return True
        return False

    def _parse_filter_selector(self, dl_filter_jpath, op):
        dl_split_jpath = dl_filter_jpath.split(op)
        dl_filter_selector = dl_split_jpath[0].strip()
        dl_filter_val = dl_split_jpath[1].strip()
        if dl_filter_selector=='$':
            dl_filter_type = None        #test itself
        elif ':' in dl_filter_selector:
            dl_filter_type = 'L'
        else:
            try:
                int(dl_filter_selector)
                dl_filter_type = 'L'
            except ValueError:
                dl_filter_type = 'D'
        return dl_filter_type, dl_filter_selector, dl_filter_val

    def _parse_filter_data(self, data, dl_type, dl_selector):
        #extract filter selector if exists
        #key?(@subkey=xxx)
        #selector: @subkey  @~subkey  @0 @-1 @1: @:5 @$
        #operator   =,  ~=,  >, <, >=, <=, in, not in
        if '?' in dl_selector:
            cond_jpath = dl_selector.split('?')
            dl_main_selector = cond_jpath[0]
            dl_filter_jpath = cond_jpath[1]
            if len(dl_filter_jpath)>2 and dl_filter_jpath[0:2]=='(@' and dl_filter_jpath[-1]==')':
                dl_filter_jpath = dl_filter_jpath[2:-1]
                op = self._parse_filter_op(dl_filter_jpath)
                if not op:
                    #operation type: subkey exists judgement
                    dl_filter_type = 'D'
                    dl_filter_selector = dl_filter_jpath.strip()
                    dl_filter_val = None
                else:
                    #operation type: = ~= >= <= in not in
                    dl_filter_type, dl_filter_selector, dl_filter_val = self._parse_filter_selector(dl_filter_jpath, op)
                #get main data
                main_data, data_level = self._atom_parse_data(data, dl_type, dl_main_selector)
                #filter by sub data testing
                #step1. get filter_data by selector
                if data_level==0:
                    if isinstance(main_data, list):
                        filter_data = []
                        for item in main_data:
                            if not dl_filter_type:
                                destitem = item
                            else:
                                destitem = self._atom_parse_data(item, dl_filter_type, dl_filter_selector)[0]
                            if self._filter_op_test(op, destitem, dl_filter_val):
                                filter_data.append(item)
                        return filter_data
                    elif isinstance(main_data, dict):
                        filter_data = dict()
                        for k, v in main_data.iteritems():
                            if not dl_filter_type:
                                destitem = v
                            else:
                                destitem = self._atom_parse_data(v, dl_filter_type, dl_filter_selector)[0]
                            if self._filter_op_test(op, destitem, dl_filter_val):
                                filter_data[k] = v
                        return filter_data
                    else:
                        return None
                else:
                    if not dl_filter_type:
                        filter_data = main_data
                    else:
                        filter_data = self._atom_parse_data(main_data, dl_filter_type, dl_filter_selector)[0]
                    #step2. test if condition ok
                    if filter_data:
                        if isinstance(filter_data, list):
                            for item in filter_data:
                                if not self._filter_op_test(op, item, dl_filter_val):
                                    return None
                            return main_data
                        elif isinstance(filter_data, dict):
                            for k, v in filter_data.iteritems():
                                if not self._filter_op_test(op, v, dl_filter_val):
                                    return None
                            return main_data
                        else:
                            if not self._filter_op_test(op, filter_data, dl_filter_val):
                                return None
                            return main_data
        return None

    def _atom_parse_data(self, data, dl_type, dl_selector):
        if dl_type=='D':
            return self._atom_parse_dict_data(data, dl_type, dl_selector)
        elif dl_type=='L':
            return self._atom_parse_list_data(data, dl_type, dl_selector)
        return None, None

    def _atom_parse_dict_data(self, data, dl_type, dl_selector):
        ret_data = None
        data_level = 0
        if dl_type == 'D' and isinstance(data, dict):
            if dl_selector[0] == '~':
                data_level = 0
                exclude_k = dl_selector[1:]
                ret_data = dict()
                for kk, vv in data.iteritems():
                    if exclude_k not in kk:
                        ret_data[kk] = vv
            else:
                data_level = 1
                ret_data = data[dl_selector] if dl_selector in data else None
        return ret_data, data_level

    def _atom_parse_list_data(self, data, dl_type, dl_selector):
        ret_data = None
        data_level = 0
        if dl_type == 'L' and isinstance(data, list):
            if ':' in dl_selector:
                data_level = 0
                range_info = dl_selector.split(':')
                if len(range_info)==2:
                    start_idx = int(range_info[0]) if range_info[0] else 0
                    end_idx = int(range_info[1]) if range_info[1] else len(data)
                    ret_data = data[start_idx:end_idx]
            else:
                data_level = 1
                single_idx = int(dl_selector)
                if single_idx>=-len(data) and single_idx<len(data):
                    ret_data = data[single_idx]
        return ret_data, data_level

    def _parse_dict_data(self, data, dl_type, dl_selector):
        ret_data = None
        if dl_type == 'D' and isinstance(data, dict):
            if '?' in dl_selector:
                #condition judgement   /D[book?(@property=xxx])]
                #/D[book?(@$=xxx)]
                return self._parse_filter_data(data, dl_type, dl_selector)
            else:
                return self._atom_parse_dict_data(data, dl_type, dl_selector)[0]
        return ret_data

    def _parse_list_data(self, data, dl_type, dl_selector):
        ret_data = None
        if dl_type == 'L' and isinstance(data, list):
            if '?' in dl_selector:
                return self._parse_filter_data(data, dl_type, dl_selector)
            else:
                return self._atom_parse_list_data(data, dl_type, dl_selector)[0]
        return ret_data

    def _get_jpath_data(self, data, jpath):
        # /D[key1]/L[0]
        # /D[~key1]/L[-1]
        # /D[key]/L[:]
        steps = [x for x in jpath.split('/') if x]
        if not steps:
            return None
        ret_data = data
        for stepinfo in steps:
            dl_type, dl_selector = self._parse_jpath(stepinfo)
            if dl_type and dl_selector:
                if dl_type == 'D' and isinstance(ret_data, dict):
                    ret_data = self._parse_dict_data(ret_data, dl_type, dl_selector)
                elif dl_type == 'D' and isinstance(ret_data, list):
                    new_ret_data = []
                    for item in ret_data:
                        new_ret_data.append(self._parse_dict_data(item, dl_type, dl_selector))
                    ret_data = new_ret_data
                elif dl_type == 'L' and isinstance(ret_data, list):
                    ret_data = self._parse_list_data(ret_data, dl_type, dl_selector)
                elif dl_type == 'L' and isinstance(ret_data, dict):
                    new_ret_data = dict()
                    for k, v in ret_data.iteritems():
                        new_ret_data[k] = self._parse_list_data(v, dl_type, dl_selector)
                    ret_data = new_ret_data
                else:
                    return None
        return ret_data

    def parse_data(self, sitename, data, dmaps):
        # '/D@data/L./D@specification'
        sitedto = self._get_sitedto_from_sitename(sitename)
        row_jpath = sitedto['row_def']['path']
        col_jpaths = sitedto['col_def']
        rows_data = self._get_jpath_data(data, row_jpath)
        if rows_data:
            row_nums = len(rows_data)
            data_rowset = []
            if isinstance(rows_data, list):
                for irow in xrange(0,row_nums):
                    data_row = {}
                    for field_name, col_jpath in col_jpaths.iteritems():
                        data_row[field_name] = self._get_jpath_data(rows_data[irow], col_jpath)
                    data_rowset.append(data_row)
            elif isinstance(rows_data, dict):
                for k, v_data in rows_data.iteritems():
                    data_row = {}
                    for field_name, col_jpath in col_jpaths.iteritems():
                        data_row[field_name] = self._get_jpath_data(v_data, col_jpath)
                    data_rowset.append(data_row)
            return data_rowset
        else:
            return None