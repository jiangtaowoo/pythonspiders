# -*- coding: utf-8 -*-
import os
import time
from sys import argv
import datetime
import functools
import yaml
import spiders.sally.updatebrandtaste as updatebrandtaste

def time_decorator(method_to_be_timed):
    def timed(*args, **kw):
        ts = time.time()
        result = method_to_be_timed(*args, **kw)
        te = time.time()
        print 'func %s took %2.4fsec' % (method_to_be_timed.__name__, te-ts)
        return result
    return timed

def addinfo_data(data, sitename, tenantname, tenantalias):
    if isinstance(data,dict):
        data['website'] = sitename
        data['tenant'] = tenantname
        data['tenantalias'] = tenantalias
        return True
    return False

def print_tips(tips, tenantalias):
    print '>>> %s getting data - %s ...' % (tenantalias, tips)

def load_tenant_info(spidername):
    app_base_dir = os.path.dirname(os.path.abspath(__file__))
    tenants = yaml.load(open(os.path.sep.join([app_base_dir, 'spiders', spidername, 'config', 'tenants.yaml'])))
    return tenants['RUN']

@time_decorator
def main(spidername='', excel_file_name=None):
    app_base_dir = os.path.dirname(os.path.abspath(__file__))
    orch_module = __import__('.'.join(['spiders', spidername, 'orchestrator.diyorch']), fromlist=[''])
    orch_cls = getattr(orch_module, 'DiyOrchestrator')
    if excel_file_name is None:
        excel_file_name = ''.join(['products_', str(datetime.date.today()), '.xlsx'])
        tenants = load_tenant_info(spidername)
        orch = orch_cls(spidername)
        for talias, tenant_item in tenants.iteritems():
            sitename = tenant_item[0]
            if len(tenant_item)>1 and 'UXIXD' in tenant_item[1]:
                tname = tenant_item[1]['UXIXD']
            else:
                tname = 'NICKNAME'
            addinfo = {'sitename': sitename, 'tenantname': tname, 'tenantalias': talias}
            orch.regist_addinfo_callback(functools.partial(addinfo_data, **addinfo))
            orch.regist_tips_callback(functools.partial(print_tips, tenantalias=talias))
            orch.setup_entry_info(tenant_item)
            orch.run_pipeline()
    #output data format
    persist_module = __import__('.'.join(['spiders', spidername, 'persistentcb']), fromlist=[''])
    if persist_module:
        persist_func = getattr(persist_module, 'sqlite_to_xlsx')
        if persist_func:
            print '>>> saving data to excel ...'
            excel_file_name = os.path.sep.join([app_base_dir, 'spiders', spidername, excel_file_name])
            persist_func(excel_file_name)
    print 'Finish!'

@time_decorator
def main_test(spidername=''):
    app_base_dir = os.path.dirname(os.path.abspath(__file__))
    orch_module = __import__('.'.join(['spiders', spidername, 'orchestrator.diyorch']), fromlist=[''])
    orch_cls = getattr(orch_module, 'DiyOrchestrator')
    tenants = load_tenant_info(spidername)
    orch = orch_cls(spidername)
    for talias, tenant_item in tenants.iteritems():
        sitename = tenant_item[0]
        tname = 'TEST'
        addinfo = {'sitename': sitename, 'tenantname': tname, 'tenantalias': talias}
        #orch.regist_addinfo_callback(functools.partial(addinfo_data, **addinfo))
        orch.regist_tips_callback(functools.partial(print_tips, tenantalias=talias))
        orch.setup_entry_info(tenant_item)
        orch.run_pipeline(isdebug=True)
    print 'Finish!'

if __name__=="__main__":
    if len(argv)>=2:
        isdebug_or_spidername = argv[1]
        if isdebug_or_spidername == 'debug' and len(argv)>2:
            spidername = argv[2]
            main_test(spidername=spidername)
        else:
            spidername = argv[1]
            updatebrandtaste.update_brand_taste()
            if len(argv)>2:
                cmd_or_excelfile = argv[2]
                if cmd_or_excelfile == 'flush' and len(argv)==4:
                    sitename = argv[3]
                    updatebrandtaste.flush_today_data(sitename)
                else:
                    excel_file_name = cmd_or_excelfile
                    if '.xlsx' in excel_file_name:
                        main(excel_file_name=excel_file_name, spidername=spidername)
            else:
                main(spidername=spidername)