# _*_ coding:utf-8 _*_
import requests
import os
import yaml
from selenium.common.exceptions import NoSuchElementException
from productmodel import ModelBase
from baseadaptor import AdaptorSqlite


class html_element_exists(object):
  def __init__(self, bywhat, id_or_name_or_xpath):
    self.bywhat = bywhat
    self.id_name_xpath = id_or_name_or_xpath

  def __call__(self, driver):
    try:
        if self.bywhat == 'id':
            element = driver.find_element_by_id(self.id_name_xpath)   # Finding the referenced element
        elif self.bywhat == 'name':
            element = driver.find_element_by_name(self.id_name_xpath)   # Finding the referenced element
        elif self.bywhat == 'xpath':
            element = driver.find_element_by_xpath(self.id_name_xpath)   # Finding the referenced element
        else:
            return False
    except NoSuchElementException:
        return False
    return element


class BaseCrawler(object):
    def __init__(self):
        self.sess = requests.session()
        app_base_dir = os.path.dirname(os.path.abspath(__file__))
        basepath = os.path.sep.join([app_base_dir,'config'])
        self.businessmodel = ModelBase()
        self.sqliteadaptor = AdaptorSqlite(spidername='tmall', dbname='comments.db')
        self.businessmodel.load_model_config(basepath + os.path.sep + 'models.yaml')
        self.sqliteadaptor.load_db_config(basepath + os.path.sep + 'dbs.yaml')
        self.businessmodel.regist_persist_adaptor(self.sqliteadaptor)
        self.accounts = yaml.load(open(basepath + os.path.sep + 'tenants.yaml'))
        if 'ACCOUNT' in self.accounts:
            self.accounts = self.accounts['ACCOUNT']
        else:
            self.accounts = None

    def _stringify_data(self, data):
        if isinstance(data, str) or isinstance(data, unicode):
            return data
        return str(data)

    def _save_browser_cookie(self, sess, browser):
        all_cookies = browser.get_cookies()
        cookies_dict = dict()
        for s_cookie in all_cookies:
            cookies_dict[s_cookie["name"]] = s_cookie["value"]
        sess.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
