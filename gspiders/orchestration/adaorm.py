# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from collections import OrderedDict
from orchestration.saveload import SaveLoader


class AdaptorORM(SaveLoader):
    def __init__(self, spidername=''):
        super(AdaptorORM, self).__init__(spidername)
        self._table_exists = []
        self.engines = dict()
        self.DBOrmCls = dict()
        self.sessions = dict()
        self.BaseCls = declarative_base()

    def _create_db_session(self, modelname):
        dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
        if dbfile not in self.engines:
            self.engines[dbfile] = create_engine("sqlite:///" + dbfile)
        #define DBORM Class
        if modelname not in self.DBOrmCls:
            self.DBOrmCls[modelname] = self._create_db_model(self.BaseCls,
                                            modelname, dbtable, pks, fieldicts)
            self.BaseCls.metadata.create_all(self.engines[dbfile])
            self.sessions[modelname] = sessionmaker(bind=self.engines[dbfile])
        return self.sessions[modelname]()

    def _create_db_model(self, BaseCls, modelname, dbtable, pks, fieldicts):
        member_dict = OrderedDict()
        member_dict['__tablename__'] = dbtable
        for colname in pks:
            member_dict[colname] = Column(String, primary_key=True)
        for colname, colrequires in fieldicts.iteritems():
            if colname in pks:
                continue
            if int(colrequires)>0:
                member_dict[colname] = Column(String, nullable=False)
            else:
                member_dict[colname] = Column(String)
        return type(modelname, (BaseCls,), member_dict)

    def is_data_exists(self, modelname, data):
        session = self._create_db_session(modelname)
        modelObj = session.query(self.DBOrmCls[modelname]).filter_by(**data).first()
        record_exists = True if modelObj else False
        session.close()
        return record_exists

    def save(self, modelname, data):
        session = self._create_db_session(modelname)
        modelObj = self.DBOrmCls[modelname](**data)
        session.add(modelObj)
        session.commit()
        session.close()

    def update(self, modelname, data):
        dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
        pkdata = dict()
        for k in pks:
            if k not in data:
                return
            pkdata[k] = data[k]
        session = self._create_db_session(modelname)
        modelObj = session.query(self.DBOrmCls[modelname]).filter_by(**pkdata).first()
        if modelObj:
            for k, v in data.iteritems():
                if k not in pks:
                    if hasattr(modelObj, k):
                        setattr(modelObj, k, v)
            session.commit()
        session.close()

    def load_data(self, modelname, filter_kwargs):
        #parse field list [col1, col2, [col3 as colX], col4]
        fieldicts = self.get_storage_config(modelname)[3]
        #query data
        session = self._create_db_session(modelname)
        modelObj_list = session.query(self.DBOrmCls[modelname]).filter_by(**filter_kwargs).all()
        dataset = []
        if modelObj_list and isinstance(modelObj_list, list):
            for modelObj in modelObj_list:
                datarow = {col:getattr(modelObj,col) for col in fieldicts if hasattr(modelObj,col)}
                dataset.append(datarow)
        session.close()
        return dataset
