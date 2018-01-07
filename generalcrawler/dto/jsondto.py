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
            if dl_type == 'D':
                ret_data = ret_data[k] if k in ret_data else None
            elif dl_type == 'L':
                if dl_ind == '@':
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

    def parse_data(self, sitename, data, dmaps):
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
                    data_row[field_name] = self._get_jpath_data(data, col_jpath, irow)
                data_rowset.append(data_row)
            return data_rowset
        else:
            return None