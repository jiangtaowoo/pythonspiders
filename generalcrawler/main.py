# -*- coding: utf-8 -*-
import os
from sys import argv
import datetime
import functools
import yaml
from orachestrator.zsorch import ZSOrchestrator
import sqlite2xlsx
import updatebrandtaste


def addinfo_data(data, sitename, tenantname, tenantalias):
    if isinstance(data,dict):
        data['website'] = sitename
        data['tenant'] = tenantname
        data['tenantalias'] = tenantalias
        return True
    return False

def print_tips(tips, tenantalias):
    print '>>> %s getting data - %s ...' % (tenantalias, tips)

def load_tenant_info():
    tenants = yaml.load(open(os.path.sep.join(['.', 'config', 'tenants.yaml'])))
    return tenants['RUN']

def main(excel_file_name=None):
    if excel_file_name is None:
        excel_file_name = ''.join(['products_', str(datetime.date.today()), '.xlsx'])
        tenants = load_tenant_info()
        orch = ZSOrchestrator()
        for talias, tenant_item in tenants.iteritems():
            sitename = tenant_item[0]
            tname = tenant_item[1]['UXIXD']
            addinfo = {'sitename': sitename, 'tenantname': tname, 'tenantalias': talias}
            orch.regist_addinfo_callback(functools.partial(addinfo_data, **addinfo))
            orch.regist_tips_callback(functools.partial(print_tips, tenantalias=talias))
            orch.setup_entry_info(tenant_item)
            orch.run_pipeline()
    print '>>> saving data to excel ...'
    sqlite2xlsx.sqlite_to_xlsx(excel_file_name, '2017-12-18')
    print 'Finish!'

if __name__=="__main__":
    if os.path.exists('products.db'):
        updatebrandtaste.update_brand_taste()
    if len(argv)==2:
        script, excel_file_name = argv
        if '.xlsx' in excel_file_name:
            main(excel_file_name)
    elif len(argv)==3:
        script, cmd, sitename = argv
        if cmd=='flush':
            updatebrandtaste.flush_today_data(sitename)
    else:
        main()