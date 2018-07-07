# -*- coding: utf-8 -*-
import sqlite3
from orchestration.saveload import SaveLoader


class AdaptorSqlite(SaveLoader):
    def __init__(self, spidername=''):
        super(AdaptorSqlite, self).__init__(spidername)
        self._table_exists = []


    def _create_table(self, modelname):
        dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
        #SQL transaction
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        sql = u'CREATE TABLE IF NOT EXISTS {0} ({1}, PRIMARY KEY ({2}));'.format(
            dbtable, u','.join([k for k in fieldicts]), u','.join(pks))
        cur.execute(sql)
        cur.close()
        conn.commit()
        conn.close()
        #mark table exists flag
        self._table_exists.append(modelname)

    @staticmethod
    def _format_sql_keqv(k, v):
        return u'{0}="{1}"'.format(k, v.replace(u'"',u"'"))

    @staticmethod
    def _gen_sql_keqv(fields, data):
        sql_cond = []
        for k in fields:
            if k not in data:
                return None
            sql_cond.append(AdaptorSqlite._format_sql_keqv(k, data[k]))
        return sql_cond

    def is_data_exists(self, modelname, data):
        record_exists = False
        if modelname in self._table_exists:
            dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
            #按主键查找数据
            sql_cond = AdaptorSqlite._gen_sql_keqv(pks, data)
            if not sql_cond:
                return False
            sql_cond = ' and '.join(sql_cond)
            conn = sqlite3.connect(dbfile)
            cur = conn.cursor()
            sql = u'select {0} from {1} where {2}'.format([k for k in fieldicts][0], dbtable, sql_cond)
            cur.execute(sql)
            for datarow in cur:
                record_exists = True
                break
            cur.close()
            conn.close()
        return record_exists

    #save a single row data
    def save(self, modelname, data):
        if modelname not in self._table_exists:
            self._create_table(modelname)
        dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
        sql_fields = []
        sql_vals = []
        for k, v in data.iteritems():
            sql_fields.append(k)
            sql_vals.append(u'"{0}"'.format(v.replace(u'"',u"'")))
        sql_fields = ','.join(sql_fields)
        sql_vals = ','.join(sql_vals)
        #SQL transaction
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        sql = u'insert into {0} ({1}) values({2})'.format(dbtable, sql_fields, sql_vals)
        cur.execute(sql)
        cur.close()
        conn.commit()
        conn.close()

    def update(self, modelname, data):
        if modelname in self._table_exists:
            dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
            sql_fields_update = []
            sql_pk_conds = AdaptorSqlite._gen_sql_keqv(pks, data)
            if not sql_pk_conds:
                return
            sql_pk_conds = ' and '.join(sql_pk_conds)
            non_pk_fields = [k for k in data if k not in pks]
            sql_fields_update = AdaptorSqlite._gen_sql_keqv(no_pk_fields, data)
            sql_fields_update = ','.join(sql_fields_update)
            #SQL transaction
            conn = sqlite3.connect(dbfile)
            cur = conn.cursor()
            sql = u'update {0} set {1} where {2}'.format(dbtable, sql_fields_update, sql_pk_conds)
            cur.execute(sql)
            cur.close()
            conn.commit()
            conn.close()

    def load_data(self, modelname, filter_kwargs):
        dbfile, dbscheme, dbtable, fieldicts, pks = self.get_storage_config(modelname)
        dataset = None
        #SQL transaction
        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        # check tablename exists
        sql = u'PRAGMA table_info(%s)' % (dbtable)
        cur.execute(sql)
        dbfields = [row[1] for row in cur]
        if dbfields:
            sql_fields = ','.join(dbfields)
            sql_cond = AdaptorSqlite._gen_sql_keqv([k for k in filter_kwargs], filter_kwargs)
            sql_cond = ' and '.join(sql_cond)
            if sql_cond:
                sql = u'select {0} from {1} where {2}'.format(sql_fields, dbtable, sql_cond)
            else:
                sql = u'select {0} from {1}'.format(sql_fields, dbtable)
            res = cur.execute(sql)
            dataset = [{dbfields[i]:x for i,x in enumerate(row)} for row in res]
        cur.close()
        conn.close()
        return dataset
