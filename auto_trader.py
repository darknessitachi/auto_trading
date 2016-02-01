# -*- encoding: utf8 -*-
# version 1.11

import math
import tkinter.messagebox
from tkinter import *
from tkinter.ttk import *
import datetime
import threading
import pickle
import winsound
import tushare as ts
import pywinauto
import pywinauto.clipboard
import pywinauto.application
from snowball_monitor import *

NUM_OF_STOCKS = 5  # 自定义股票数量
is_start = False
is_monitor = True
set_stocks_info = []
actual_stocks_info = []
consignation_info = []
is_ordered = [1] * NUM_OF_STOCKS  # 1：未下单  0：已下单
is_dealt = [0] * NUM_OF_STOCKS  # 0: 未成交   负整数：卖出数量， 正整数：买入数量
stock_codes = [''] * NUM_OF_STOCKS


class OperationThs:
    def __init__(self):
        self.__app = pywinauto.application.Application()
        self.__app.connect(title='网上股票交易系统5.0')
        top_hwnd = pywinauto.findwindows.find_window(title='网上股票交易系统5.0')
        dialog_hwnd = pywinauto.findwindows.find_windows(top_level_only=False, class_name='#32770', parent=top_hwnd)[0]
        wanted_hwnds = pywinauto.findwindows.find_windows(top_level_only=False, parent=dialog_hwnd)
        # print('wanted_hwnds length', len(wanted_hwnds))
        if len(wanted_hwnds) not in (99, 97, 96, 100):
            tkinter.messagebox.showerror('错误', '无法获得同花顺双向委托界面的窗口句柄')
        self.__main_window = self.__app.window_(handle=top_hwnd)
        self.__dialog_window = self.__app.window_(handle=dialog_hwnd)

    def __buy(self, code, quantity):
        """买函数
        :param code: 代码， 字符串
        :param quantity: 数量， 字符串
        """
        self.__dialog_window.Edit1.SetFocus()
        time.sleep(0.2)
        self.__dialog_window.Edit1.SetEditText(code)
        time.sleep(0.2)
        if quantity != '0':
            self.__dialog_window.Edit3.SetEditText(quantity)
            time.sleep(0.2)
        self.__dialog_window.Button1.Click()
        time.sleep(0.2)

    def __sell(self, code, quantity):
        """
        卖函数
        :param code: 股票代码， 字符串
        :param quantity: 数量， 字符串
        """
        self.__dialog_window.Edit4.SetFocus()
        time.sleep(0.2)
        self.__dialog_window.Edit4.SetEditText(code)
        time.sleep(0.2)
        if quantity != '0':
            self.__dialog_window.Edit6.SetEditText(quantity)
            time.sleep(0.2)
        self.__dialog_window.Button2.Click()
        time.sleep(0.2)

    def __closePopupWindow(self):
        """
        关闭一个弹窗。
        :return: 如果有弹出式对话框，返回True，否则返回False
        """
        popup_hwnd = self.__main_window.PopupWindow()
        if popup_hwnd:
            popup_window = self.__app.window_(handle=popup_hwnd)
            popup_window.SetFocus()
            popup_window.Button.Click()
            return True
        return False

    def __closePopupWindows(self):
        """
        关闭多个弹出窗口
        :return:
        """
        while self.__closePopupWindow():
            time.sleep(0.5)

    def order(self, code, direction, quantity):
        """
        下单函数
        :param code: 股票代码， 字符串
        :param direction: 买卖方向， 字符串
        :param quantity: 买卖数量， 字符串
        """
        if direction == 'B':
            self.__buy(code, quantity)
        if direction == 'S':
            self.__sell(code, quantity)
        self.__closePopupWindows()

    def maxWindow(self):
        """
        最大化窗口
        """
        if self.__main_window.GetShowState() != 3:
            self.__main_window.Maximize()
        self.__main_window.SetFocus()

    def minWindow(self):
        """
        最小化窗体
        """
        if self.__main_window.GetShowState() != 2:
            self.__main_window.Minimize()

    def refresh(self, t=0.5):
        """
        点击刷新按钮
        :param t:刷新后的等待时间
        """
        self.__dialog_window.Button5.Click()
        time.sleep(t)

    def getMoney(self):
        """
        获取可用资金
        """
        return float(self.__dialog_window.Static19.WindowText())

    @staticmethod
    def __cleanClipboardData(data, cols=11):
        """
        清洗剪贴板数据
        :param data: 数据
        :param cols: 列数
        :return: 清洗后的数据，返回列表
        """
        lst = data.strip().split()[:-1]
        matrix = []
        for i in range(0, len(lst) // cols):
            matrix.append(lst[i * cols:(i + 1) * cols])
        return matrix[1:]

    def __copyToClipboard(self):
        """
        拷贝持仓信息至剪贴板
        :return:
        """
        self.__dialog_window.CVirtualGridCtrl.RightClick(coords=(30, 30))
        self.__main_window.TypeKeys('C')

    def __getCleanedData(self):
        """
        读取ListView中的信息
        :return: 清洗后的数据
        """
        self.__copyToClipboard()
        data = pywinauto.clipboard.GetData()
        return self.__cleanClipboardData(data)

    def __selectWindow(self, choice):
        """
        选择tab窗口信息
        :param choice: 选择个标签页。持仓，撤单，委托，成交
        :return:
        """
        rect = self.__dialog_window.CCustomTabCtrl.ClientRect()
        x = rect.width() // 8
        y = rect.height() // 2
        if choice == 'W':
            x = x
        elif choice == 'E':
            x *= 3
        elif choice == 'R':
            x *= 5
        elif choice == 'A':
            x *= 7
        self.__dialog_window.CCustomTabCtrl.ClickInput(coords=(x, y))
        time.sleep(0.5)

    def __getInfo(self, choice):
        """
        获取股票信息
        """
        self.__selectWindow(choice=choice)
        return self.__getCleanedData()

    def getPosition(self):
        """
        获取持仓
        :return:
        """
        return self.__getInfo(choice='W')

    @staticmethod
    def getDeal(code, pre_position, cur_position):
        """
        获取成交数量
        :param code: 需检查的股票代码， 字符串
        :param pre_position: 下单前的持仓
        :param cur_position: 下单后的持仓
        :return: 0-未成交， 正整数是买入的数量， 负整数是卖出的数量
        """
        if pre_position == cur_position:
            return 0
        pre_len = len(pre_position)
        cur_len = len(cur_position)
        if pre_len == cur_len:
            for row in range(cur_len):
                if cur_position[row][0] == code:
                    return int(float(cur_position[row][1]) - float(pre_position[row][1]))
        if cur_len > pre_len:
            return int(float(cur_position[-1][1]))

    def withdraw(self, code, direction):
        """
        指定撤单
        :param code: 股票代码
        :param direction: 方向 B， S
        :return:
        """
        row_pos = []
        info = self.__getInfo(choice='R')
        if direction == 'B':
            direction = '买入'
        elif direction == 'S':
            direction = '卖出'
        if info:
            for index, element in enumerate(info):
                if element[0] == code:
                    if element[1] == direction:
                        row_pos.append(index)
        if row_pos:
            for row in row_pos:
                self.__dialog_window.CVirtualGridCtrl.ClickInput(coords=(7, 28 + 16 * row))
            self.__dialog_window.Button12.Click()
            self.__closePopupWindows()

    def withdrawBuy(self):
        """
        撤买
        :return:
        """
        self.__selectWindow(choice='R')
        self.__dialog_window.Button8.Click()
        self.__closePopupWindows()

    def withdrawSell(self):
        """
        撤卖
        :return:
        """
        self.__selectWindow(choice='R')
        self.__dialog_window.Button9.Click()
        self.__closePopupWindows()

    def withdrawAll(self):
        """
        全撤
        :return:
        """
        self.__selectWindow(choice='R')
        self.__dialog_window.Button7.Click()
        self.__closePopupWindows()

def auto_trade():
    count = 0
    try:
        operation = OperationThs()
        operation.maxWindow()
        pre_position = operation.getPosition()
        position = format_position(pre_position)
        money = operation.getMoney()
    except:
        tkinter.messagebox.showerror('错误', '无法获得交易软件句柄')
    monitor = snowball_monitor()
    while 1:
        na = monitor.get_new_adjustment()
        if na is not None:
            # sell
            for stock_symbol in na['group_history']:
                single_adjustment = na['group_history'][stock_symbol]
                if single_adjustment['prev_weight'] > single_adjustment['target_weight'] and \
                    stock_symbol in position and position[stock_symbol] > 0:
                    quantity = calculate_sell_quantity(stock_symbol, single_adjustment, position[stock_symbol])
                    order([stock_symbol, 'S', quantity], operation)
                    winsound.Beep(800, 800)
            # buy
            for stock_symbol in na['group_history']:
                single_adjustment = na['group_history'][stock_symbol]
                if single_adjustment['prev_weight'] < single_adjustment['target_weight']:
                    quantity = calculate_buy_quantity(stock_symbol, single_adjustment, money)
                    order([stock_symbol, 'B', quantity], operation)
                    winsound.Beep(800, 800)
        time.sleep(1.5)
        count += 1
        print(count)
        if count % 200 == 0:
            operation.refresh()


def format_position(position):
    formatted_position = {}
    for r in position:
        formatted_position[r[3]] = [r[6]]
    return formatted_position

def order(new_adjustment, operation):
    try:
        operation.maxWindow()
        operation.order(new_adjustment)
        operation.refresh()
    except:
        return False
    return True

def calculate_buy_quantity(stock_symbol, single_adjustment, money):
    p_w, t_w = single_adjustment['prev_weight'], single_adjustment['target_weight']
    while 1:
        stock_price = get_stock_realtime_price(stock_symbol)
        if stock_price is not None:
            price = ['a5_p'][0]
            break
    if p_w / t_w <= 0.3:
        return 0
    elif p_w / t_w >= 0.8:
        return math.floor(money/price/100)*100
    else:
        return (p_w/t_w*money/price)//100*100

def calculate_sell_quantity(stock_symbol, single_adjustment, position):
    p_w, t_w = single_adjustment['prev_weight'], single_adjustment['target_weight']
    if (t_w == 0) or (p_w / t_w <= 0.3):
        return position
    elif p_w / t_w >= 0.8:
        return 0
    else:
        return (p_w/t_w*position)//100*100

def get_stock_realtime_price(stock_symbol):
    try:
        df = ts.get_realtime_quotes(stock_symbol)
    except:
        return None
    return df

if __name__ == '__main__':
    t = threading.Thread(target=auto_trade)
    t.start()