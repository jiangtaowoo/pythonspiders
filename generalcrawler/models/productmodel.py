# -*- coding: utf-8 -*-
import os
import hashlib
import yaml

class ModelBase(object):
    def __init__(self):
        self._persist_adaptor = None    #持久化的适配器需要注册到类, 在类认为适当的时候调用持久化接口
        self._models_cfg = None         #model configuration
        #self._pk = None
        #self._fields_name = None        #dict
        self._pk_data = None            #primary key data
        self._fields_data = None        #对象实际数据, dict类型

    def load_model_config(self, model_yaml_cfg_filepath):
        if os.path.exists(model_yaml_cfg_filepath):
            self._models_cfg = yaml.load(open(model_yaml_cfg_filepath,'r'))
            return True
        return False

    def _get_specific_model(self, modelname):
        (pk, fields_name) = (None, None)
        if modelname in self._models_cfg:
            pk = self._models_cfg[modelname]['PK']
            fields_name = self._models_cfg[modelname]['cols']
        return pk, fields_name

    def _gen_model_data(self, modelname, **kwargs):
        def beautiful_str_data(xdata):
            if isinstance(xdata, unicode):
                return xdata.encode('utf-8')
            else:
                return str(xdata)
        pk, fields_name = self._get_specific_model(modelname)
        (self._pk_data, self._fields_data) = (dict(), dict())
        for fname, fval in fields_name.iteritems():
            if isinstance(fval,list):
                fields_data = []
                for subfname in fval:
                    if subfname in kwargs:
                        fields_data.append(beautiful_str_data(kwargs[subfname]))
                    else:
                        break
                self._fields_data[fname] = hashlib.md5('jtwu'.join(fields_data)).hexdigest()
            else:
                if fval and fname not in kwargs:
                    #必填字段空缺
                    self._fields_data = None
                    break
                else:
                    if fname in kwargs:
                        self._fields_data[fname] = beautiful_str_data(kwargs[fname])
        if self._fields_data:   #generate pk data
            for k in pk:
                if k in self._fields_data:
                    self._pk_data[k] = self._fields_data[k]
                else:
                    self._pk_data = None
                    break
            #self._pk_data = {k: v for k, v in self._fields_data.iteritems() if k in pk}

    def regist_persist_adaptor(self, persist_adaptor):
        self._persist_adaptor = persist_adaptor

    def notify_model_info_debug(self, av_data_module, **kwargs):
        #just print the model info
        for modelname, modelcfg in self._models_cfg.iteritems():
            if modelname in av_data_module:
                self._gen_model_data(modelname, **kwargs)
                if self._fields_data is not None:
                    for k, v in self._fields_data.iteritems():
                        print k, '=', v

    def notify_model_info_received(self, av_data_module, **kwargs):
        for modelname, modelcfg in self._models_cfg.iteritems():
            if modelname in av_data_module:
                self._gen_model_data(modelname, **kwargs)
                if self._pk_data is not None and self._fields_data is not None:
                    if not self._persist_adaptor.data_exists(modelname, modelcfg, **self._pk_data):
                        self._persist_adaptor.save_data(modelname, modelcfg, **self._fields_data)

    def notify_model_info_end(self):
        self._persist_adaptor.close_database()
