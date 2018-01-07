# -*- coding: utf-8 -*-
import os
import yaml
from dto.htmldto import HtmlDTO
from dto.jsondto import JsonDTO

class DTOManager(object):
    def __init__(self):
        self._dto_cfgs = []
        self._cb_funcs = {}    # self._cb_funcs['www.baidu.com']['funcxxname'] = func_xxx
        self._cb_objs = {}    # self._cb_objs['www.baidu.com'] = obj_cb_baidu
        self._http_data_types = {}     # {'sitename': {'sitehttp': datatype}}
        self.jsondto = None         # basedto is a pass through dto
        self.htmldto = None         # basedto is a pass through dto

    def _get_sitedto_from_sitename(self, sitename):
        if sitename in self._dto_cfgs:
            return self._dto_cfgs[sitename]
        return None

    def _load_dto_callback(self):
        if self._dto_cfgs:
            for sitename, sitedto in self._dto_cfgs.iteritems():
                cb_model, cb_class = None, None
                if 'callback' in sitedto and 'classinfo' in sitedto['callback']:
                    cb_modname = sitedto['callback']['classinfo']['modulename']
                    cb_clsname = sitedto['callback']['classinfo']['classname']
                    cb_model = __import__('dto.' + cb_modname, fromlist=[''])
                    cb_class = getattr(cb_model, cb_clsname)
                    self._cb_objs[sitename] = cb_class()
                if cb_model and cb_class:
                    cb_funcs = dict()
                    self._cb_funcs[sitename] = cb_funcs
                    http_datatype = dict()
                    self._http_data_types[sitename] = http_datatype
                    # load callback functions
                    for httptype, callbackinfo in sitedto['callback']['httpinfo'].iteritems():
                        for k, v in callbackinfo.iteritems():
                            if k=='data_type':
                                http_datatype[httptype] = v
                            else:
                                if v:
                                    cb_funcs[v] = getattr(cb_class, v)
                    # load diy columns callback functions
                    if 'col_calc' in sitedto:
                        col_calcs = sitedto['col_calc']
                        for field_name, calc_info in col_calcs.iteritems():
                            cb_funcname = calc_info[0]
                            if cb_funcname not in cb_funcs:
                                cb_funcs[cb_funcname] = getattr(cb_class, cb_funcname)

    def load_dto_config(self, dto_cfg_file_path):
        if os.path.exists(dto_cfg_file_path):
            self._dto_cfgs = yaml.load(open(dto_cfg_file_path, 'r'))
            self._load_dto_callback()
            self.jsondto = JsonDTO()
            self.htmldto = HtmlDTO()
            self.jsondto.load_dto_config(dto_cfg_file_path)
            self.htmldto.load_dto_config(dto_cfg_file_path)
            return True
        return False

    def _parse_diydata(self, sitename, data, dmaps):
        # '/D@data/L./D@specification'
        sitedto = self._dto_cfgs[sitename] if sitename in self._dto_cfgs else None
        col_calcs = None
        if 'col_calc' in sitedto:
            col_calcs = sitedto['col_calc']             #column calculated by exist column
        if isinstance(data,list) and col_calcs:
            for data_row in data:
                for field_name, calc_info in col_calcs.iteritems():
                    cb_col_func = None
                    params = []
                    params.append(self._cb_objs[sitename])
                    for idx, x in enumerate(calc_info):
                        if idx == 0:
                            cb_col_func = self._cb_funcs[sitename][x]
                        else:
                            if x in data_row:              # 1st prior: column data by column name
                                params.append(data_row[x])
                            else:
                                if x in dmaps:               # 2nd prior: dmaps data by key
                                    params.append(dmaps[x])
                                else:
                                    params.append(x)         # 3rd prior: raw data
                    if cb_col_func:
                        data_row[field_name] = cb_col_func(*params)
        return data

    def exec_callback(self, data, run_info):
        (tips, sitename, sitehttp, dmaps, sleepinterval) = run_info
        if sitename not in self._dto_cfgs:
            return None, None
        if sitehttp not in self._http_data_types[sitename]:
            return None, None
        #step 1. general next url and dynamic datamapping
        cb_generatorname = self._dto_cfgs[sitename]['callback']['httpinfo'][sitehttp]['generatorfunc']
        cb_site_obj = self._cb_objs[sitename]
        cb_generator_func = self._cb_funcs[sitename][cb_generatorname] if cb_generatorname else None
        if cb_generator_func:
            next_run_info = cb_generator_func(cb_site_obj, data, dmaps)
        #step 2. pre-process data in callback class
        cb_funcname = self._dto_cfgs[sitename]['callback']['httpinfo'][sitehttp]['callbackfunc']
        cb_func = self._cb_funcs[sitename][cb_funcname] if cb_funcname else None
        if cb_func:
            data = cb_func(cb_site_obj, data)
        #step 3. process data in general style for json or html
        datatype = self._http_data_types[sitename][sitehttp]
        if data:
            if datatype == 'json' and self.jsondto:
                data = self.jsondto.parse_data(sitename, data, dmaps)
            elif datatype == 'html' and self.htmldto:
                data = self.htmldto.parse_data(sitename, data, dmaps)
            else:
                data = None
        #step 4. process diy column info
        if data:
            data = self._parse_diydata(sitename, data, dmaps)
        #step 5. return nexturl and data
        if not data and sitehttp is not 'login_http':
            next_run_info = None
        return next_run_info, data