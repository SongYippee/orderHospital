# -*- coding: utf-8 -*-
# @Time    : 2018/11/9 10:15
# @Software: PyCharm
import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from hospitals import hospitals


class SZ12320(object):
    def __init__(self,name,id):
        self.browser = webdriver.Chrome()
        self.name = name
        self.id = id

    def step1(self):
        url = "http://www.jssz12320.cn:8080/hrs/step01"
        self.browser.get(url)
        self.browser.find_element_by_id("id").send_keys(self.id)
        self.browser.find_element_by_id("name").send_keys(self.name)
        phone = self.browser.find_element_by_id("phone")
        phone.click()
        # option = Select(browser.find_element_by_id("medicalType"))
        # option.select_by_value(u"市民卡")
        self.browser.find_element_by_class_name("submit-btn").submit()

    def step2(self):
        self.browser.find_element_by_xpath("//img[@code='ZYYY']").click()

    def setp3(self):
        doctorName = u"陈剑平"
        self.browser.find_element_by_id("docName").send_keys(doctorName)
        self.browser.find_element_by_id("button").click()
        btns = self.browser.find_elements_by_class_name("btnUnfull")
        # btns = self.browser.find_elements_by_class_name("btnFull") # 预约已满
        for btn in btns:
            onclick = btn.get_attribute('onclick')
            print type(onclick)
            print onclick
        btns[0].click()
        time.sleep(3)
        canOrders = self.browser.find_elements_by_xpath("//img[@title]")
        for e in canOrders:
            print e.get_attribute('onclick')

if __name__ == "__main__":
    sz = SZ12320(u"your name",u"your ID number")
    sz.step1()
    sz.step2()
    sz.setp3()