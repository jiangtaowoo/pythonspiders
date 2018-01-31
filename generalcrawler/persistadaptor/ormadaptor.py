# -*- coding: UTF-8 -*-
import os
#import copy
import yaml
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from collections import OrderedDict
#import time

class AdaptorORM(object):
    def __init__(self, spidername='', dbname='products.db'):
        app_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._models_cfg = None
        self._db_name = os.path.sep.join([app_base_dir, 'spiders', spidername, dbname])
        self._tb_name_exists = []
        self.bTbCreated = False
        #self.cur_ts = int(time.time())
        self.engine=create_engine("sqlite:///" + self._db_name)
        self.DBSession = sessionmaker(bind=self.engine)
        self.BaseCls = declarative_base()
        self.DBOrmCls = dict()

    def close_database(self):
        pass

    def _create_db_model(self, BaseCls, modelname, modelcfg):
        member_dict = OrderedDict()
        if 'tablename' in modelcfg:
            member_dict['__tablename__'] = modelcfg['tablename']
        if 'PK' in modelcfg:
            for colname in modelcfg['PK']:
                member_dict[colname] = Column(String, primary_key=True)
        if 'cols' in modelcfg:
            for colname, colrequires in modelcfg['cols'].iteritems():
                if colname in modelcfg['PK']:
                    continue
                if isinstance(colrequires,list) or int(colrequires)>0:
                    member_dict[colname] = Column(String, nullable=False)
                else:
                    member_dict[colname] = Column(String)
        return type(modelname, (BaseCls,), member_dict)

    def _filter_model_data(self, modelname, modelcfg, **kwargs):
        if modelname in self._models_cfg:
            #modelcfg = self._models_cfg[modelname]
            if 'cols' in modelcfg:
                valid_data = dict() #copy.deepcopy(kwargs)
                for k, v in kwargs.iteritems():
                    if k in modelcfg['cols']:
                        valid_data[k] = v if not isinstance(v, str) else v.decode('utf-8')
                return valid_data
        return None

    def load_db_config(self, model_yaml_config_filepath):
        if os.path.exists(model_yaml_config_filepath):
            model_cfgs = yaml.load(open(model_yaml_config_filepath))
            #define DBORM Class
            self.DBOrmCls = dict()
            for modelname, modelcfg in model_cfgs.iteritems():
                self.DBOrmCls[modelname] = self._create_db_model(self.BaseCls, modelname, modelcfg)
            self.BaseCls.metadata.create_all(self.engine)
            self._models_cfg = model_cfgs

    def save_data(self, modelname, modelcfg, **kwargs):
        if modelname in self._models_cfg:
            tbname = self._models_cfg[modelname]['tablename']
            session = self.DBSession()
            valid_data = self._filter_model_data(modelname, modelcfg, **kwargs)
            modelObj = self.DBOrmCls[modelname](**valid_data)
            session.add(modelObj)
            session.commit()
            session.close()

    def update_data(self, modelname, modelcfg, pk_data_d, **kwargs):
        if modelname in self._models_cfg and pk_data_d is not None:
            tbname = self._models_cfg[modelname]['tablename']
            session = self.DBSession()
            modelObj = session.query(self.DBOrmCls[modelname]).filter_by(**pk_data_d).first()
            if modelObj:
                for k, v in kwargs.iteritems():
                    if k not in pk_data_d:
                        if hasattr(modelObj, k):
                            setattr(modelObj, k, v if not isinstance(v, str) else v.decode('utf-8'))
                session.commit()
            session.close()

    def data_exists(self, modelname, modelcfg, **kwargs):
        session = self.DBSession()
        if modelname in self._models_cfg:
            tbname = self._models_cfg[modelname]['tablename']
            modelObj = session.query(self.DBOrmCls[modelname]).filter_by(**kwargs).first()
            if modelObj:
                session.close()
                return True
        session.close()
        return False

    def load_data(self, tablename, fieldslist, **kwargs):
        #parse field list [col1, col2, [col3 as colX], col4]
        fieldnames = []
        fieldnameass = []
        if isinstance(fieldslist,list):
            for field_item in fieldslist:
                if isinstance(field_item,list):
                    fname = field_item[0]
                    fnameas = field_item[1]
                    fieldnames.append(fname)
                    fieldnameass.append(fnameas)
                else:
                    fname = field_item
                    fieldnames.append(fname)
                    fieldnameass.append(fname)
        #find dest model
        dst_modelname = ''
        dst_modelcfg = ''
        for modelname, modelcfg in self._models_cfg.iteritems():
            if tablename == modelcfg['tablename']:
                dst_modelname = modelname
                dst_modelcfg = modelcfg
                break
        #query data
        session = self.DBSession()
        valid_cond_data = self._filter_model_data( dst_modelname, dst_modelcfg, **kwargs)
        modelObj_list = session.query(self.DBOrmCls[dst_modelname]).filter_by(**valid_cond_data).all()
        dataset = []
        if modelObj_list and isinstance(modelObj_list, list):
            for modelObj in modelObj_list:
                datarow = [getattr(modelObj,col) for col in fieldnames]
            data_set.append(datarow)
        session.close()
        return fieldnameass, dataset