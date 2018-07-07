# -*- coding: utf-8 -*-
from meta.metacls import Singleton
from meta.setting import ConfigManager
from dto.htmldto import HtmlDTO
from dto.jsondto import JsonDTO
from dto.rawdto import RawDTO

class DTOManager(object):
    __metaclass__ = Singleton

    def __init__(self):
        cfgm = ConfigManager()
        self.spidername = cfgm.spidername
        self._dto_cfgs = cfgm.get_spider_config(self.spidername)['dto']
        self._cb_funcs = dict() #self._cb_funcs['baidu.com']['fname'] = func_xxx
        self._cb_objs = dict()  #self._cb_objs['baidu.com'] = class_inst_baidu

    def load_dto_callback(self):
        if not self._dto_cfgs:
            return None
        cls_instances = dict()
        for runnerid, dtocfg in self._dto_cfgs.iteritems():
            if 'callback' in dtocfg:
                name_module = dtocfg['callback']['modulename']
                name_class = dtocfg['callback']['classname']
                key = name_module + '.' + name_class
                #step1. load callback model, class
                if key in cls_instances:
                    cb_class, cls_inst = cls_instances[key]
                else:
                    cb_model = __import__('spiders.{0}.{1}'.format(
                        self.spidername, name_module), fromlist=[''])
                    cb_class = getattr(cb_model, name_class)
                    cls_inst = cb_class()
                    cls_instances[key] = (cb_class, cls_inst)
                #step2. load callback procedure
                funcs = dict()
                for name_func in dtocfg['callback']['procedure']:
                    funcs[name_func] = getattr(cb_class, name_func)
                #step3. assignment to memeber variables
                self._cb_objs[runnerid] = cls_inst
                self._cb_funcs[runnerid] = funcs

    def get_dto_config(self, runner):
        runnerid = runner.id
        if self._dto_cfgs and runnerid in self._dto_cfgs:
            return self._dto_cfgs[runnerid]
        return None

    def get_data_models(self, runner):
        dtocfg = self.get_dto_config(runner)
        return dtocfg['datamodule'] if 'datamodule' in dtocfg else None

    @staticmethod
    def get_dto_class(dtocfg):
        if 'datatype' in dtocfg['field']:
            datatype = dtocfg['field']['datatype']
            if datatype=="json":
                return JsonDTO
            elif datatype=="html":
                return HtmlDTO
            elif datatype=="raw":
                return RawDTO
        return None

    @staticmethod
    def get_row_path(dtocfg):
        if 'row_def' in dtocfg['field']:
            return dtocfg['field']['row_def']
        return None

    @staticmethod
    def get_col_paths(dtocfg):
        if 'col_def' in dtocfg['field']:
            return dtocfg['field']['col_def']
        return None

    @staticmethod
    def get_col_diys(dtocfg):
        if 'col_calc' in dtocfg['field']:
            return dtocfg['field']['col_calc']
        return None

    #调用callback自定义函数， 计算自定义字段
    def parse_diydata(self, runner, data):
        # '/D@data/L./D@specification'
        if not self._cb_objs:
            self.load_dto_callback()
        runnerid = runner.id
        dtocfg = self.get_dto_config(runner)
        col_calcs = DTOManager.get_col_diys(dtocfg)
        if col_calcs and isinstance(data,list):
            for data_row in data:
                for field_name, (funcname, ps) in col_calcs.iteritems():
                    func = self._cb_funcs[runnerid][funcname]
                    params = []
                    params.append(self._cb_objs[runnerid])  #1st param: self
                    params.append(runner)                   #2nd param: runner
                    for p in ps:
                        params.append(data_row[p] if p in data_row else p)
                    data_row[field_name] = func(*params)
        return data

    def extract_data(self, runner, data):
        dtocfg = self.get_dto_config(runner)
        DTOClass = DTOManager.get_dto_class(dtocfg)
        row_path = DTOManager.get_row_path(dtocfg)
        col_paths = DTOManager.get_col_paths(dtocfg)
        if DTOClass:
            data = DTOClass.parse_data(data, row_path, col_paths)
            data = self.parse_diydata(runner, data)
            return data
        else:
            return None
