# -*- coding: utf-8 -*-
from basedto import BaseDTO

class JsonDTO(BaseDTO):
    def _get_jpath_data(self, data, jpath, cur_row_idx=0):
        steps = [x for x in jpath.split('/') if x]
        ret_data = data
        for stepinfo in steps:
            dl_type = stepinfo[0]
            dl_ind = stepinfo[1]
            k = str(stepinfo[2:])
            if dl_type == 'D' and isinstance(ret_data, dict):
                if dl_ind == '@':
                    if k[0] == '~':
                        exclude_k = k[1:]
                        new_ret_data = dict()
                        for kk, vv in ret_data.iteritems():
                            if exclude_k not in kk:
                                new_ret_data[kk] = vv
                        ret_data = new_ret_data
                    else:
                        ret_data = ret_data[k] if k in ret_data else None
            elif dl_type == 'L' and isinstance(ret_data, list):
                if dl_ind == '@':
                    if k[0] == '~':
                        exclude_k = int(k[1:])
                        del ret_data[exclude_k]
                        return ret_data
                    elif k == 'last()':
                        cur_row_idx = len(ret_data)-1
                    else:
                        cur_row_idx = int(k)
                    if cur_row_idx<len(ret_data):
                        ret_data = ret_data[cur_row_idx]
                    else:
                        return None
            else:
                return None
            if ret_data is None:
                return None
        return ret_data

    def parse_data_v0(self, sitename, data, dmaps):
        # '/D@data/L./D@specification'
        sitedto = self._get_sitedto_from_sitename(sitename)
        row_jpath = sitedto['row_def']['path']
        col_jpaths = sitedto['col_def']
        row_data = self._get_jpath_data(data, row_jpath)
        if row_data:
            row_nums = len(row_data)
            data_rowset = []
            for irow in xrange(0,row_nums):
                data_row = {}
                for field_name, col_jpath in col_jpaths.iteritems():
                    data_row[field_name] = self._get_jpath_data(row_data, col_jpath, irow)
                data_rowset.append(data_row)
            return data_rowset
        else:
            return None

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