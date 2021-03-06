# -*- coding: utf-8 -*-
import os
import time
import pickle
import base64
import requests
from sys import argv
from PIL import Image
import pytesseract
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.common.proxy import Proxy


class xpath_element_exists(object):
  def __init__(self, xpath):
    self.xpath = xpath

  def __call__(self, driver):
    try:
        element = driver.find_element_by_xpath(self.xpath)   # Finding the referenced element
    except NoSuchElementException:
        return False
    return element


def calc_proxy_profile(proxy_info, drivertype='phantomjs'):
    if drivertype=='chrome':
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=http://%s' % (proxy_info))
        return chrome_options
    elif drivertype=='firefox':
        profile = webdriver.FirefoxProfile()
        proxyobj = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_info,
        'ftpProxy': proxy_info,
        'sslProxy': proxy_info,
        'noProxy': '' # set this value as desired
        })
        profile.set_proxy(proxyobj)
        profile.update_preferences()
        return profile
    serv_args = ['--proxy=%s' % (proxy_info), '--proxy-type=http',]
    #'--proxy-auth=username:password'
    return serv_args

def save_captcha(captcha_file_path, browser, img_xpath):
    ele_captcha = browser.find_element_by_xpath(img_xpath)
    img_captcha_base64 = browser.execute_async_script("""
        var ele = arguments[0], callback = arguments[1];
        ele.addEventListener('load', function fn(){
          ele.removeEventListener('load', fn, false);
          var cnv = document.createElement('canvas');
          cnv.width = this.width; cnv.height = this.height;
          cnv.getContext('2d').drawImage(this, 0, 0);
          callback(cnv.toDataURL('image/jpeg').substring(22));
        }, false);
        ele.dispatchEvent(new Event('load'));
        """, ele_captcha)
    with open(captcha_file_path, 'wb') as f:
        f.write(base64.b64decode(img_captcha_base64))

def recognize_captcha(captcha_file_path):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    captcha = pytesseract.image_to_string(Image.open(captcha_file_path), config='outputbase digits')
    return captcha

def get_prod_filename(themonth, id, datatype=None):
    if datatype is None:
        return ''.join(['.', os.sep, 'dataout', os.sep, str(themonth), os.sep, str(id), '.html'])
    else:
        return ''.join(['.', os.sep, 'dataout', os.sep, 'sfda_', str(datatype), '_', str(themonth), '.log'])

def save_data(browser, themonth, id):
    with open(get_prod_filename(themonth,id),'w') as outf:
        outf.write(browser.page_source.encode('utf-8'))

def load_download_complete_info():
    filepath = ''.join(['.', os.sep, 'dataout', os.sep, 'sfda_complete.log'])
    completedict = dict()
    if os.path.exists(filepath):
        completedict = pickle.load(open(filepath,'rb'))
    return completedict

def update_download_complete_info(themonth, pageidx):
    filepath = ''.join(['.', os.sep, 'dataout', os.sep, 'sfda_complete.log'])
    completedict = dict()
    if os.path.exists(filepath):
        completedict = pickle.load(open(filepath,'rb'))
    if str(themonth) in completedict:
        pagelist = completedict[str(themonth)]
        if int(pageidx) not in pagelist:
            pagelist.append(int(pageidx))
            pagelist.sort()
    else:
        completedict[str(themonth)] = [int(pageidx)]
    pickle.dump(completedict, open(filepath,'wb'))

def get_product_xpath():
    i = 1
    while i<30:
        yield '//table//tr[%d]/td/p/a' % (i)
        i += 2

def get_product_id(hrefinfo):
    idx1 = hrefinfo.rindex('Id=')+3
    hrefinfo = hrefinfo[idx1:]
    idx2 = hrefinfo.index("'")
    return hrefinfo[:idx2]

def add_log(themonth, *args):
    with open(get_prod_filename(themonth, 0, 'trace'), 'a+') as outf:
        xlist = []
        for x in args:
            if isinstance(x,unicode):
                xlist.append(x.encode('utf-8'))
            else:
                xlist.append(str(x))
        msg_log = '\t'.join(xlist)
        outf.write(msg_log)
        outf.write('\n')
        print '   >>> ' + msg_log

def save_prod_order_info(themonth, prod_id, pageidx, reset=False):
    if reset:
        fname = get_prod_filename(themonth, 0, 'order')
        if os.path.exists(fname):
            os.remove(fname)
    else:
        with open(get_prod_filename(themonth, 0, 'order'), 'a+') as outf:
            outf.write('\t'.join([str(prod_id), str(pageidx)]))
            outf.write('\n')

def get_data_page(browser, themonth, pageidx):
    captcha_file_path = 'captcha_' + str(themonth) + '.jpg'
    btn_detail_xpath = '//table//tr/td[2]/a[contains(@href,"123.127")]'
    captcha_xpath = '//img[contains(@src,"randomImage")]'
    btn_input_captcha = '//input[contains(@name,"randomInt")]'
    btn_send_captcha = '//div[@class="btnGroup"]/a[@class="check"]'
    btn_return_list = '//img[contains(@src,"data_fanhui")]'
    next_page_xpath = '//img[contains(@src,"dataanniu_07")]'
    page_info_xpath = '//img[contains(@src,"dataanniu_03")]/parent::td/preceding-sibling::td[2]'
    elem_page_info = WebDriverWait(browser, 10).until(xpath_element_exists(page_info_xpath))
    #elem_page_info = browser.find_element_by_xpath(page_info_xpath)
    page_info = elem_page_info.text
    page_info = page_info[page_info.index(u'共')+1:]
    page_info = page_info[:page_info.index(u'页')]
    page_total = int(page_info)
    if pageidx<1 or pageidx>page_total:
        return None
    #load no prod details info
    no_details_prod_list = []
    try:
        with open(get_prod_filename(themonth, 0, 'nodetails')) as infile:
            for line in infile:
                if '\t' in line:
                    no_details_prod_list.append( line.strip().split('\t')[0] )
    except:
      pass
    print '- getting data for page %d of %d' % (pageidx, page_total)
    elem_page = browser.find_element_by_id('goInt')
    elem_page.clear()
    elem_page.send_keys(str(pageidx))
    goto_page_xpath = '//input[contains(@src,"dataanniu_11")]'
    elem_gotopage = browser.find_element_by_xpath(goto_page_xpath)
    elem_gotopage.click()
    product_xpaths = get_product_xpath()
    prod_xpath = product_xpaths.next()
    elem = WebDriverWait(browser, 10).until(xpath_element_exists(prod_xpath))
    product_xpaths = get_product_xpath()
    #判断本页是否已经下载完成, 如果是, 后续不需要再访问该页
    page_download_complete = True
    for prod_xpath in product_xpaths:
        #a. get one line of products, open to get details
        try:
            elem_prod = browser.find_element_by_xpath(prod_xpath)
            prod_name = elem_prod.text.encode('utf-8')
            prod_id = get_product_id(elem_prod.get_attribute('href'))
            prod_data_path = get_prod_filename(themonth, prod_id)
            if os.path.exists(prod_data_path):
                save_prod_order_info(themonth, prod_id, pageidx)
                continue
            if str(prod_id) in no_details_prod_list:
                continue
            #还有数据未下载, 该页未完全下载
            page_download_complete = False
            save_prod_order_info(themonth, prod_id, pageidx)
            elem_prod.click()
        except NoSuchElementException:
            break
        #time.sleep(3)
        #b. click details
        WebDriverWait(browser, 10).until(xpath_element_exists(btn_detail_xpath))
        elem_detail = browser.find_element_by_xpath(btn_detail_xpath)
        elem_detail.click()
        #time.sleep(3)
        #c.1 wait for captcha
        while len(browser.window_handles)<2:
            time.sleep(1)
        browser.switch_to.window(browser.window_handles[1])
        prod_url = None
        while prod_url is None or 'ShowJSYQAction.do' not in prod_url:
            time.sleep(1)
            prod_url = browser.current_url
        captcha_wrong = True
        try_times = 0
        while captcha_wrong and try_times<5:
            elem = WebDriverWait(browser, 10).until(xpath_element_exists(captcha_xpath))
            #c.2 save captcha, recognize captcha
            save_captcha(captcha_file_path, browser, captcha_xpath)
            captcha = recognize_captcha(captcha_file_path)
            #c.3 input keys
            elem_inputcaptch = browser.find_element_by_xpath(btn_input_captcha)
            elem_inputcaptch.send_keys(captcha)
            #c.4 send keys
            elem_sendcaptch = browser.find_element_by_xpath(btn_send_captcha)
            elem_sendcaptch.click()
            try:
                WebDriverWait(browser, 10).until(xpath_element_exists('//body'))
                save_data(browser, themonth, prod_id)
                #prod_url = browser.current_url
                add_log(themonth, str(pageidx), str(prod_id), prod_name, prod_url)
                captcha_wrong = False
            except UnexpectedAlertPresentException:
                try:
                    WebDriverWait(browser, 3).until(EC.alert_is_present(),
                                           'Timed out waiting for PA creation ' +
                                           'confirmation popup to appear.')
                    alert = browser.switch_to.alert
                    alert.accept()
                    try_times += 1
                    if len(browser.window_handles)==1:
                        captcha_wrong = False
                        add_log(themonth, str(pageidx), str(prod_id), prod_name, "No product details")
                except TimeoutException:
                    print("no alert")
        if captcha_wrong:
            add_log(themonth, str(pageidx), str(prod_id), prod_name, "Failed")
        os.remove(captcha_file_path)
        #d. close tab
        if len(browser.window_handles)>1:
            browser.close()
        browser.switch_to.window(browser.window_handles[0])
        elem_return = browser.find_element_by_xpath(btn_return_list)
        elem_return.click()
        #time.sleep(3)
    if page_download_complete:
        update_download_complete_info(themonth, pageidx)
    return True


def main(themonth, pageidx):
    url = 'http://app1.sfda.gov.cn/datasearch/face3/base.jsp?tableId=69&tableName=TABLE69&title=%BD%F8%BF%DA%BB%AF%D7%B1%C6%B7&bcId=124053679279972677481528707165'
    input_search_xpath = '//input[contains(@type,"text") and contains(@name,"COLUMN811")]'
    btn_search_xpath = '//input[@name="COLUMN805"]/following-sibling::input'
    search_keys = u'国妆备进字J2018' + str(themonth)
    #step1. open website
    browser = webdriver.Firefox()
    proxy_info = None
    #browser = webdriver.Firefox(firefox_profile=calc_proxy_profile(proxy_info, 'firefox'))
    #browser = webdriver.Chrome(chrome_options=calc_proxy_profile(proxy_info, 'chrome'))
    #browser = webdriver.PhantomJS(service_args=calc_proxy_profile(proxy_info, 'phantomjs'))
    browser.get(url)
    #加载已经下载完成的页面信息, 避免多次重复打开这些页面
    completedict = load_download_complete_info()
    month_complete_list = []
    if str(themonth) in completedict:
        month_complete_list = completedict[str(themonth)]
    try:
        #step2. query by category
        elem = WebDriverWait(browser, 10).until(xpath_element_exists(input_search_xpath))
        #elem = browser.find_element_by_xpath(input_search_xpath)
        elem.send_keys(search_keys)
        elem = browser.find_element_by_xpath(btn_search_xpath)
        elem.click()
        #step3. find product one by one
        has_data = True
        while has_data:
            if pageidx not in month_complete_list:
                has_data = get_data_page(browser, themonth, pageidx)
            pageidx += 1
            #time.sleep(120)
        browser.quit()
        return True
    except:
        browser.quit()
        return False


if __name__=="__main__":
    if len(argv)==3:
        script, themonth, pageidx = argv
        main(themonth, int(pageidx))
    elif len(argv)==2:
        script, themonth = argv
        month_list = xrange(int(themonth),4)
        i = 0
        #for i in xrange(int(themonth),4):
        while True:
            print '>>> cata %d ---' % (i)
            save_prod_order_info(i, 0, 0, True)
            if main(i, 1):
                i = i+1
            if i>=len(month_list):
              break
