#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests
import time
import winsound
from PyQt4 import QtGui


#global variables

s = 0

request_tag = 0

proxy_tag = 0

pa_history = []

basic_url = 'http://xueqiu.com/cubes/rebalancing/history.json'

b2_url = 'http://xueqiu.com/v4/stock/quotec.json?code=VNM%2CYINN%2CYANG%2CFXP&_='

group_list = [ \
#    {'id': 0, 'url': 'ZH018320', 'name': '正安'}, \
#    {'id': 1, 'url': 'ZH670387', 'name': '趋势为基量价先行'}, \
#    {'id': 0, 'url': 'ZH000859', 'name': 'while1'}, \
    {'id': 0, 'url': 'ZH771938', 'name': '冷刃不血3英吉沙'} \
#    {'id': 1, 'url': 'ZH201028', 'name': '短线'} \
#    {'id': 4, 'url': 'ZH149523', 'name': '满仓股'} \
#    {'id': 2, 'url': 'ZH064714', 'name': '模拟'}, \
#    {'id': 3, 'url': 'ZH573797', 'name': '股灾后'}, \
#    {'id': 4, 'url': 'ZH005627', 'name': '捝取一号'} \
]

cookies = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
}

headers1 = {
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': '*/*',
    'Referer': 'http://xueqiu.com/',
    'Accept-Language': 'zh-CN',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Host': 'xueqiu.com',
    'DNT': '1',
    'Connection': 'Keep-Alive'
}

headers2 = {
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'http://xueqiu.com/',
    'Accept-Language': 'zh-CN',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Host': 'xueqiu.com',
    'DNT': '1',
    'Connection': 'Keep-Alive',
    'Pragma': 'no-cache'
}

Proxy_list = [ \
#    '114.215.141.103:3128', \
    'http://115.28.73.197:3128' \
]

p = {'areacode' : '86',
     'username' : 'jizy10@163.com',
     'password' : 'AD0C1F9A32F1B60F2154C76733F14CD0',
     'remember_me' : 'on'
    }

#functions

def initialize_cookies():
    global cookies, s
    s = requests.Session()
    r = s.get('http://www.xueqiu.com', headers = headers)
    cookies = r.cookies

def initialize_position_adjustment_history():
    global pa_history
    pa_history = get_position_adjustment_history()


def get_position_adjustment_history():
    global pa_history
    for group in group_list:
        group_history = get_group_adjustment_history(group)
        pop_group_history(group['id'], group_history)
    return pa_history

def get_group_adjustment_history(group, need_check = None):
    global request_tag
    params = load_params(group['url'])
    proxies = load_proxies()
    success = False
    while success is not True:
        try:
            r = s.get(basic_url, params = params, headers = headers, timeout = 6)
        except:
#            error = str(requests.exceptions.Timeout)
#            app = QtGui.QApplication(sys.argv)
#            msgBox = QtGui.QMessageBox()
#            msgBox.setText(u'连接失败！')
#            msgBox.show()
#            app.exec_()
            print('sb')
        else:
            success = True
    request_tag += 1
    print(request_tag)
    content = r.json()
    group_history = mine_group_history(group['id'], content, need_check = need_check)
    return group_history

def mine_group_history(group_id, content, need_check):
    global pa_history
    ga_id = content['list'][0]['id']
    if need_check:
        if ga_id == pa_history[group_id]['id']:
            return None
    local_time = time.asctime(time.localtime(int(content['list'][0]['created_at'])/1000))
    group_history_raw = content['list'][0]['rebalancing_histories']
    group_history = {'id':ga_id, 'group_id':group_id, 'group_name':group_list[group_id]['name'], 'time':local_time, 'history': {}}
    for stock in group_history_raw:
        group_history['history'][stock['stock_symbol']] = {'name'         : stock['stock_name'], \
                                                           'price'        : stock['price'], \
                                                           'prev_weight'  : stock['prev_weight'], \
                                                           'target_weight': stock['target_weight'] \
        }
    if need_check:
        pa_history[group_id] = group_history
    return group_history

def pop_group_history(group_id, group_history):
    global pa_history
    if len(pa_history) == group_id:
        pa_history.append(group_history)
    else:
        pa_history[group_id] = group_history

def load_params(group_url):
    params = {'cube_symbol': group_url, \
              'count'      : '20', \
              'page'       : '1' \
    }
    return params

def load_proxies():
    global proxy_tag
    if proxy_tag == len(Proxy_list):
        proxy_tag = 0
        return None
    proxy_tag += 1
    return {'http': Proxy_list[proxy_tag-1]}

def login():
    r = s.get('http://xueqiu.com/service/csrf?api=http%3A%2F%2Fxueqiu.com%2Fuser%2Flogin HTTP/1.1', headers = headers)
    r3 = s.post('http://xueqiu.com/user/login', data = p, headers = headers2)

def run_strategy():
    for group in group_list:
        group_history = get_group_adjustment_history(group, True)
        if group_history is not None:
            winsound.Beep(800, 800)
            msgBox = QtGui.QMessageBox()
            text = group_history['group_name'] + '\n' + str(group_history['time'])
            for stock_symbol in group_history['history']:
                text += '\n' + stock_symbol
                text += '\t' + group_history['history'][stock_symbol]['name']
                text += '\t' + str(group_history['history'][stock_symbol]['price'])
                text += '\t' + str(group_history['history'][stock_symbol]['prev_weight'])
                text += '->' + str(group_history['history'][stock_symbol]['target_weight'])
            msgBox.setText(text)
            msgBox.exec_()
        time.sleep(2.5)

if __name__ == '__main__':
    winsound.Beep(800, 800)

    initialize_cookies()

    login()

    initialize_position_adjustment_history()

    app = QtGui.QApplication(sys.argv)

    while 1:
        run_strategy()
