# -*- coding: utf-8 -*-
from basedto import BaseDTO

class JsonDTO(BaseDTO):
    def _parse_jpath(self, jpath_segment):
        dl_type = jpath_segment[0]
        dl_ind = jpath_segment[1:]
        if len(dl_ind)>1 and dl_ind[0]=='[' and dl_ind[-1]==']':
            dl_key = dl_ind[1:-1]
            if len(dl_key)>0:
                return dl_type, dl_key
        return None, None

    def _parse_dict_data(self, data, dl_type, dl_key):
        ret_data = None
        if dl_type == 'D' and isinstance(data, dict):
            if dl_key[0] == '~':
                exclude_k = dl_key[1:]
                ret_data = dict()
                for kk, vv in data.iteritems():
                    if exclude_k not in kk:
                        ret_data[kk] = vv
            else:
                ret_data = data[dl_key] if dl_key in data else None
        return ret_data

    def _parse_list_data(self, data, dl_type, dl_key):
        ret_data = None
        if dl_type == 'L' and isinstance(data, list):
            if ':' in dl_key:
                range_info = dl_key.split(':')
                if len(range_info)==2:
                    if range_info[0]:
                        start_idx = int(range_info[0])
                    else:
                        start_idx = 0
                    if range_info[1]:
                        end_idx = int(range_info[1])
                    else:
                        end_idx = len(data)
                    ret_data = data[start_idx:end_idx]
            else:
                single_idx = int(dl_key)
                if single_idx>=-len(data) and single_idx<len(data):
                    ret_data = data[single_idx]
        return ret_data

    def _get_jpath_data(self, data, jpath):
        # /D[key1]/L[0]
        # /D[~key1]/L[-1]
        # /D[key]/L[:]
        steps = [x for x in jpath.split('/') if x]
        ret_data = data
        for stepinfo in steps:
            dl_type, dl_key = self._parse_jpath(stepinfo)
            if dl_type and dl_key:
                if dl_type == 'D' and isinstance(ret_data, dict):
                    ret_data = self._parse_dict_data(ret_data, dl_type, dl_key)
                elif dl_type == 'D' and isinstance(ret_data, list):
                    new_ret_data = []
                    for item in ret_data:
                        new_ret_data.append(self._parse_dict_data(item, dl_type, dl_key))
                    ret_data = new_ret_data
                elif dl_type == 'L' and isinstance(ret_data, list):
                    ret_data = self._parse_list_data(ret_data, dl_type, dl_key)
                elif dl_type == 'L' and isinstance(ret_data, dict):
                    new_ret_data = dict()
                    for k, v in ret_data.iteritems():
                        new_ret_data[k] = self._parse_list_data(v, dl_type, dl_key)
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