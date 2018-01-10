# -*- coding: utf-8 -*-
import os
import yaml
import sqlite3
import datetime


def load_brand_taste_cfg(brand_taste_cfg_file):
    if os.path.exists(brand_taste_cfg_file):
        brand_taste_data = yaml.load(open(brand_taste_cfg_file))
        brand_data = brand_taste_data['brand']
        taste_data = brand_taste_data['taste']
        brand_data.sort(key=lambda x: -len(x))
        taste_data.sort(key=lambda x: -len(x))
        return brand_data, taste_data
    return None, None

def update_colval(db_file_path, colname, vallist):
    if os.path.exists(db_file_path):
        conn = sqlite3.connect(db_file_path)
        cur = conn.cursor()
        sql = 'select internal_id, productname, %s from prod_details where %s=""' % (colname, colname)
        res = cur.execute(sql)
        data_map = dict()       #map internal_id to value
        for data_row in res:
            prodname = data_row[1]
            for v in vallist:
                if v in prodname:
                    data_map[data_row[0]] = v
                    break
        cur.close()
        cur = conn.cursor()
        for k, v in data_map.iteritems():
            sql = 'update prod_details set %s="%s" where internal_id="%s"' % (colname, v, k)
            res = cur.execute(sql)
            #if res.rowcount>0:
            #    print k, v
        cur.close()
        conn.commit()
        conn.close()
        
def update_brand_taste():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_file_path = os.path.sep.join([current_dir, 'config', 'taste.yaml'])
    db_file_path = os.path.sep.join([current_dir, 'products.db'])
    brand_data, taste_data = load_brand_taste_cfg(cfg_file_path)
    update_colval(db_file_path, 'product_brand', brand_data)
    update_colval(db_file_path, 'product_taste', taste_data)
    #print 'Fininsh!'

def flush_today_data(website):
    dateinfo = str(datetime.date.today())
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_file_path = os.path.sep.join([current_dir, 'products.db'])
    if os.path.exists(db_file_path):
        conn = sqlite3.connect(db_file_path)
        cur = conn.cursor()
        sql = 'delete from prod_price where website like "%' + website + '%" and public_date="' + dateinfo + '"'
        cur.execute(sql)
        cur.close()
        conn.commit()
        conn.close()