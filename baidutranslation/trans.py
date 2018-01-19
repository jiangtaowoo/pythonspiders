# -*- coding: UTF-8 -*-
import os
from sys import argv
import time
import json
import yaml
#import copy
#import collections
#import urllib
#import lxml.html
import requests
import fanyi_sign

def time_decorator(method_to_be_timed):
    def timed(*args, **kw):
        ts = time.time()
        result = method_to_be_timed(*args, **kw)
        te = time.time()
        print 'func %s took %2.4fsec' % (method_to_be_timed.__name__, te-ts)
        return result
    return timed

class html_element_exists(object):
    def __init__(self, bywhat, id_or_name_or_xpath):
        self.bywhat = bywhat
        self.id_name_xpath = id_or_name_or_xpath

    def __call__(self, driver):
        from selenium.common.exceptions import NoSuchElementException
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
    
    
@time_decorator
def main_selenium(filename='wordlist.txt'):
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    url = 'https://fanyi.baidu.com'
    urlbase = 'https://fanyi.baidu.com/#zh/en/'
    words = load_words(filename)
    dr = webdriver.Firefox()
    dr.get(url)
    words_result = []
    result_xpath = '//p[contains(@class,"target-output")]/span'
    for word in words:
        dr.get( urlbase + word )
        elem = WebDriverWait(dr, 60).until(html_element_exists('xpath', result_xpath))
        words_result.append(elem.text)
        dr.get(url)
    for idx, word in enumerate(words):
        print word, words_result[idx]
    dr.quit()

"""
def get_js_var(rsp):
    if not isinstance(rsp,str) and not isinstance(rsp,unicode):
        txt = rsp.text
    else:
        txt = rsp
    idx1 = txt.index('window.gtk')
    window_gtk = str(txt[idx1:idx1+50].split(';')[0].split('=')[1].strip().replace("'",''))
    idx2 = txt.index('token:')
    token = str(txt[idx2:idx2+50].split(',')[0].split(':')[1].strip().replace("'",""))
    js_var_dict = dict()
    js_var_dict['token'] = str(token)
    js_var_dict['gtk'] = str(window_gtk)
    return js_var_dict

def first_visit(sess, url, headers):
    return sess.get(url, headers=headers)
"""

def load_words(filename):
    #return yaml.load(open(filename))['words']
    return yaml.load(open(filename)).split(' ')

def get_payload(js_var_dict, word):
    token = js_var_dict['token']
    window_gtk = js_var_dict['gtk']
    sign = fanyi_sign.calc_sign(word, window_gtk)
    payload = dict()#collections.OrderedDict()
    payload['from'] = 'zh'
    payload['to'] = 'en'
    payload['query'] = word
    payload['simple_means_flag'] = '3'
    payload['sign'] = sign
    payload['token'] = token
    #payload['query'] = urllib.quote(word.encode('utf-8'))
    return payload

def translate(sess, url, headers, payload):
    rsp = sess.post(url, headers=headers, data=payload)
    try:
        return json.loads(rsp.text)['trans_result']['data'][0]['dst']
    except:
        print payload
        print rsp.text
        return None

def load_valid_cookie():
    cookies_dict = dict()
    cookies_dict['BAIDUID'] = 'F2D26E6860E87B9920DCFD8FD6E16C96:FG=1'
    cookies_dict['BIDUPSID'] = 'F2D26E6860E87B9920DCFD8FD6E16C96'
    cookies_dict['PSTM'] = '1511952139'
    cookies_dict['cflag'] = '15:3'
    cookies_dict['locale'] = 'zh'
    cookies_dict['from_lang_often'] = '%5B%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%2C%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%5D'
    cookies_dict['to_lang_often'] =  '%5B%7B%22value%22%3A%22zh%22%2C%22text%22%3A%22%u4E2D%u6587%22%7D%2C%7B%22value%22%3A%22en%22%2C%22text%22%3A%22%u82F1%u8BED%22%7D%5D'
    cookies_dict['REALTIME_TRANS_SWITCH']='1'
    cookies_dict['FANYI_WORD_SWITCH']='1'
    cookies_dict['HISTORY_SWITCH']='1'
    cookies_dict['SOUND_SPD_SWITCH']='1'
    cookies_dict['SOUND_PREFER_SWITCH']='1'
    cookies_dict['Hm_lvt_64ecd82404c51e03dc91cb9e8c025574'] = '1516367312,1516371326,1516372831'
    cookies_dict['Hm_lpvt_64ecd82404c51e03dc91cb9e8c025574'] ='1516372905'
    return cookies_dict

@time_decorator
def main(filename='wordlist.txt'):
    url = 'https://fanyi.baidu.com'
    #urllangdetect = 'http://fanyi.baidu.com/langdetect'
    urlapi = 'http://fanyi.baidu.com/v2transapi'
    words = load_words(filename)
    headers = {'Host': 'fanyi.baidu.com', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2', 'Connection': 'keep-alive'}
    #headers = copy.deepcopy(headers)
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    headers['Referer'] = 'http://fanyi.baidu.com/'
    headers['X-Requested-With'] = 'XMLHttpRequest'
    sess = requests.session()
    #rsp = first_visit(sess, url, headers)

    #update cookie
    sess.cookies = requests.utils.cookiejar_from_dict(load_valid_cookie())
    #js_var_dict = get_js_var(rsp)
    js_var_dict = dict()
    js_var_dict['gtk'] = "320305.131321201"
    js_var_dict['token'] = '327dadb43ba01fe117bd0350a0b28af9'
    #step 1.
    tran_results = []
    for word in words:
        #step 2.
        payload = get_payload(js_var_dict, word)
        transed_word = translate(sess, urlapi, headers, payload)
        tran_results.append(transed_word)
        #break
    for idx, word in enumerate(words):
        print words[idx], tran_results[idx]
        #break
        
if __name__=="__main__":
    if len(argv)==1:
        main()
    elif len(argv)==2:
        script, filename = argv
        if os.path.exists(filename):
            main(filename)
    elif len(argv)==3:
        script, filename, param = argv
        if os.path.exists(filename) and param=='debug':
            main_selenium(filename)