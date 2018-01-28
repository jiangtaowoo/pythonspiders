# _*_ coding:utf-8 _*_
import os
import datetime
from sys import argv
import yaml
from TmallSpider import TMallCrawler
import sqlite2xlsx

def main():
    tmallCrawlerObj = TMallCrawler()
    tenants = load_tenant_info()
    for sitename, siteinfo in tenants.iteritems():
        for iteminfo in siteinfo:
            for prodname, produrl in iteminfo.iteritems():
                tmallCrawlerObj.crawl_tmall_comment(sitename, prodname, produrl)

def load_tenant_info():
    app_base_dir = os.path.dirname(os.path.abspath(__file__))
    tenants = yaml.load(open(os.path.sep.join([app_base_dir, 'config', 'tenants.yaml'])))
    return tenants['RUN']

if __name__ == '__main__':
    if len(argv)==2:
        script, excel_file_name = argv
        if '.xlsx' in excel_file_name:
            sqlite2xlsx.sqlite_to_xlsx(excel_file_name)
            print 'Finish excel output!'
    else:
        main()
        excel_file_name = ''.join(['comments_', str(datetime.date.today()), '.xlsx'])
        sqlite2xlsx.sqlite_to_xlsx(excel_file_name)
        print 'Finish excel output!'