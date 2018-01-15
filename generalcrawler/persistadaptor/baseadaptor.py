# -*- coding: utf-8 -*-
import os
import yaml
import sqlite3
import time

class AdaptorSqlite(object):
    def __init__(self, spidername='', dbname='products.db'):
        app_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._dbs_cfg = None
        self._db_name = os.path.sep.join([app_base_dir, 'spiders', spidername, dbname])
        self._tb_name_exists = []
        self.conn = None
        self.cur_ts = int(time.time())

    def open_database(self):
        if not self.conn:
            self.conn = sqlite3.connect(self._db_name)

    def close_database(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def commit_database(self):
        if self.conn:
            #ts = int(time.time())
            #if ts-self.cur_ts > 60:
                #self.cur_ts = ts
            self.conn.commit()

    def _create_table(self, tbname, pk, fieldsname):
        sql_fields = ','.join(fieldsname)
        sql_pk = ','.join(pk)
        if not self.conn:
            self.open_database()
        cur = self.conn.cursor()
        sql = 'CREATE TABLE IF NOT EXISTS %s (%s, PRIMARY KEY (%s));' % (tbname, sql_fields, sql_pk)
        cur.execute(sql)
        cur.close()
        self.conn.commit()
        #conn.close()

    def load_db_config(self, db_yaml_config_filepath):
        if os.path.exists(db_yaml_config_filepath):
            self._dbs_cfg = yaml.load(open(db_yaml_config_filepath,'r'))

    def save_data(self, modelname, modelcfg, **kwargs):
        if modelname in self._dbs_cfg:
            tbname = self._dbs_cfg[modelname]['tablename']
            sql_fields = []
            sql_vals = []
            for k, v in kwargs.iteritems():
                sql_fields.append(str(k))
                if isinstance(v,unicode):
                    sql_vals.append('"' + v.encode('utf-8').replace('"',"'") + '"')
                else:
                    sql_vals.append('"' + str(v).replace('"',"'") + '"')
            sql_fields = ','.join(sql_fields)
            sql_vals = ','.join(sql_vals)
            if not self.conn:
                self.open_database()
            #conn = sqlite3.connect(self._db_name)
            cur = self.conn.cursor()
            sql = "insert into %s (%s) values(%s)" % (tbname, sql_fields, sql_vals)
            cur.execute(sql)
            cur.close()
            ts = int(time.time())
            if ts-self.cur_ts > 60:
                self.cur_ts = ts
                self.commit_database()
            #conn.commit()
            #conn.close()

    def data_exists(self, modelname, modelcfg, **kwargs):
        record_exists = False
        if modelname in self._dbs_cfg:
            tbname = self._dbs_cfg[modelname]['tablename']
            if tbname not in self._tb_name_exists:
                #create table if not exists
                pk = modelcfg['PK']
                fieldsname = [k for k, v in modelcfg['cols'].iteritems()]
                self._create_table(tbname, pk, fieldsname)
                self._tb_name_exists.append(tbname)
            sql_cond = [str(k) + "='" + str(v) + "'" for k,v in kwargs.iteritems()]  #[col1='val1', col2='val2']
            sql_cond = ' and '.join(sql_cond)                           #col1='val1' and col2='val2'
            if not self.conn:
                self.open_database()
            #conn = sqlite3.connect(self._db_name)
            cur = self.conn.cursor()
            sql = "select * from %s where %s" % (tbname, sql_cond)
            cur.execute(sql)
            for datarow in cur:
                record_exists = True
                break
            cur.close()
            #conn.close()
        return record_exists

    def load_data(self, tablename, fieldslist, **kwargs):
        load_fail_ret = False
        if not self.conn:
            self.open_database()
        #conn = sqlite3.connect(self._db_name)
        cur = self.conn.cursor()
        # check tablename exists
        sql = 'PRAGMA table_info(%s)' % (tablename)
        cur.execute(sql)
        fieldsname_org = [row[1] for row in cur]
        fieldnames = []
        sql_col = []
        sql_cond = []
        if fieldsname_org and isinstance(fieldslist,list):
            for field_item in fieldslist:
                if isinstance(field_item,list):
                    fname = field_item[0]
                    fnameas = field_item[1]
                    fieldnames.append(fnameas)
                    sql_col.append(fname + ' as ' + fnameas)
                else:
                    fname = field_item
                    fieldnames.append(fname)
                    sql_col.append(fname)
                if fname not in fieldsname_org:
                    load_fail_ret = True
                    break
        else:
            load_fail_ret = True
        if not load_fail_ret:
            sql_col = ', '.join(sql_col)
            if kwargs:
                for fname, fval in kwargs.iteritems():
                    sql_cond.append(fname + '="' + fval + '"')
                sql_cond = ' and '.join(sql_cond)
                sql = 'select ' + sql_col + ' from ' + tablename + ' where ' + sql_cond
            else:
                sql = 'select ' + sql_col + ' from ' + tablename
            res = cur.execute(sql)
            data_set = [[x for x in row] for row in res]
            if data_set:
                cur.close()
                #conn.close()
                self.close_database()
                return fieldnames, data_set
        cur.close()
        #conn.close()
        self.close_database()
        return None, None