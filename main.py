# -*- coding:utf-8 -*-

import requests
import sys
import logging
from urllib import urlencode
import re
import json
import time
import hospitals
from mylogger import MyLogger

MyLogger(show_console=True)


class SuDaHospital(object):
    '''苏州大学第一附属医院，十梓街院'''

    def __init__(self, user=None, doctor=None):
        self.user = user
        self.doctor = doctor
        self.session = requests.Session()
        headers = {}
        headers['Accept'] = '*/*'
        headers['Accept-Encoding'] = 'gzip, deflate'
        headers['Cache-Control'] = 'no-cache'
        headers['DNT'] = '1'
        headers['Host'] = 'new.sdfyy.cn'
        headers['Origin'] = 'http://new.sdfyy.cn'
        headers['Pragma'] = 'no-cache'
        headers['Upgrade-Insecure-Requests'] = '1'
        headers[
            "User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
        self.headers = headers

    def __login(self):
        login_url = "http://new.sdfyy.cn/preregister/login.html"
        headers = dict()
        headers['Referer'] = 'http://new.sdfyy.cn/appointment'
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Requested-With'] = 'XMLHttpRequest'
        self.headers.update(headers)

        data = {
            "card_num": self.user['id'],
            "password": self.user['password'],
            "response_type": '9'
        }
        response = self.session.post(login_url, headers=self.headers, data=data, timeout=60)
        logging.info(u"登录状态 %s, URL：%s" % (str(response.status_code), response.url))
        self.session.cookies.update(response.cookies)
        if response.status_code != 200:
            logging.error(u"登录失败")
            sys.exit(0)
        if response.content.find(self.user['name'].encode('utf-8')):
            status = True
        else:
            status = False
        return status

    def __logout(self):
        req = self.session.get("http://new.sdfyy.cn/preregister/logout.html")
        print logging.info(u"退出")

    def __initDoctor(self):
        '''
        初始化医生，关键是获取doctor的code和url
        :return:
        '''
        searchUrl = "http://new.sdfyy.cn/appointment/localhost/sdfyy/index.php?s=/Appointment/search"
        self.headers['Referer'] = 'http://new.sdfyy.cn/appointment/index.html'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        post_data = {
            'keyword': self.doctor['name'],
            'search_type': 1,
            'page': 1
        }
        response = self.session.post(searchUrl, data=post_data, headers=self.headers)
        self.headers.pop('X-Requested-With')
        logging.info(u"查询医生状态：%s, URL: %s" % (str(response.status_code), response.url))
        if response.status_code != 200:
            logging.error(u"查询医生失败" + response.text)
            sys.exit(0)

        result = json.loads(response.content)
        if result['code'] != 200:
            logging.error(u'初始化医生信息失败\n')
            sys.exit(0)
        code = result['data'][0]['code']
        deptcode = result['data'][0]['deptcode']
        deptname = result['data'][0]['deptname']
        docURL = "http://new.sdfyy.cn/appointment/index.php?s=/doctor/index/id/" + str(code)
        self.doctor['code'] = code
        self.doctor['url'] = docURL
        self.doctor['deptname'] = deptname
        self.doctor['deptcode'] = deptcode

    def __orderDoctor(self):
        if 'url' not in self.doctor:
            self.__initDoctor()
        self.headers['Referer'] = 'http://new.sdfyy.cn/appointment/index.html'
        # 访问医生页面，获取可预约的日期
        response = self.session.get(self.doctor['url'], headers=self.headers)
        logging.info(u"访问医生页面状态: %s, URL: %s" % (str(response.status_code), response.url))
        if response.status_code != 200:
            logging.error(u"访问医生页面失败" + response.text)
            sys.exit(0)

        def getCanOrderDateList(content):
            '''
            查询医生可预约日期列表
            :param content:
            :return:
            '''
            a = re.findall(r"\<span class=\"hospital-name ...\"\>(.*?)\<\/span\>", content)
            # print a
            b = re.findall(r"\<span class=\"typename\"\>(.*?)\<\/span\>", content)
            # print b
            c = re.findall(r"class=\"hospital-id\" value=\"(.*?)\"\>", content)
            # print c
            d = re.findall(r"\<span class=\"clinic-fee\"\>(.*?)\<\/span\>", content)
            # print d
            e = re.findall(r"class=\"unit-name\" value=\"(.*?)\"\>", content)
            # print e
            f = re.findall(r"class=\"unit-code\" value=\"(.*?)\"\>", content)
            # print f
            g = re.findall(r"class=\"charge-type\" value=\"(.*?)\"\>", content)
            # print g
            h = re.findall(r"class=\"charge-type-name\" value=\"(.*?)\"\>", content)
            # print h
            i = re.findall(r"class=\"request-day\" value=\"(.*?)\"\>", content)
            # print i
            j = re.findall(r"class=\"ampm\" value=\"(.*?)\"\>", content)
            # print j
            dateList = []
            if len(a) == len(b) == len(c) == len(d) == len(e) == len(f) == len(g) == len(h) == len(i) == len(j):
                for index in range(len(a)):
                    detail = {}
                    detail['hospitalName'] = unicode(a[index].strip(), "utf-8")
                    detail['typeName'] = unicode(b[index].strip(), "utf-8")
                    detail['hospitalId'] = unicode(c[index].strip(), "utf-8")
                    detail['clinicFee'] = unicode(d[index].strip(), "utf-8")
                    detail['unitName'] = unicode(e[index].strip(), "utf-8")
                    detail['unitCode'] = unicode(f[index].strip(), "utf-8")
                    detail['chargeType'] = unicode(g[index].strip(' '), "utf-8")
                    detail['chargeTypeName'] = unicode(h[index].strip(' '), "utf-8")
                    detail['date'] = unicode(i[index].strip()[0:10], "utf-8")
                    detail['ampm'] = unicode(j[index].strip(), "utf-8")
                    dateList.append(detail)
            return dateList

        def getCanOrderTimeList(dateDetail):
            '''
            查询指定日期内，可预约的时间段
            :param dateDetail:
            :return:
            '''
            timeUrl = "http://new.sdfyy.cn/appointment/index.php?s=/Home/Interface/worktime&callback=timedetailcallback&unit_code=" + str(
                dateDetail['unitCode']) + "&doctor_code=" + self.doctor['code'] + "&charge_type=" + dateDetail[
                          'chargeType'] + "+&ampm=" + dateDetail['ampm'] + "&request_day=" + dateDetail[
                          'date'] + "&hospital_id=" + dateDetail['hospitalId'] + "&_=" + format(time.time() * 1000,
                                                                                                '.0f')
            self.headers['Referer'] = self.doctor['url']
            self.headers['X-Requested-With'] = 'XMLHttpRequest'
            response = self.session.get(timeUrl, headers=self.headers)
            self.headers.pop('X-Requested-With')
            logging.info(u"查询 %s 可预约时段状态: %s, URL: %s" % (dateDetail['date'], str(response.status_code), response.url))

            def parseTimeDetail(content):
                content = content[content.find('(') + 1:-1]
                message = json.loads(content)
                if message['code'] != 200:
                    print "error"
                    sys.exit(0)
                result = []
                for _ in message['data']:
                    if int(_['leftnum']) > 0:
                        result.append(_)
                return result

            return parseTimeDetail(response.content)

        dateList = getCanOrderDateList(response.content)

        if self.user['date']:
            dateList = [x for x in dateList if x['date'] == self.user['date']]

        if dateList:
            for eachDate in dateList:
                timeList = getCanOrderTimeList(eachDate)
                if timeList:
                    for eachTime in timeList:
                        if self.__realOrder(eachDate, eachTime):
                            logging.info(u"预约成功，%s %s - %s %s" % (eachDate['date'], eachTime['starttime'], eachTime[
                                'endtime'], self.doctor['name']))
                            return
                else:
                    logging.info(u'%s这天，%s医生的号已排满，无法预约' % (eachDate['date'], self.doctor['name']))
                    continue

        else:
            logging.info(u"当前没有 %s 医生的可预约日期" % (self.doctor['name'],))

    def __realOrder(self, dateDetail, timeDetail):
        '''预约医生'''
        confirmPage = 'http://new.sdfyy.cn/preregister/reservesubmit?'
        data = {
            'hospital_name': dateDetail['hospitalName'].encode('utf-8'),
            'hospital_id': dateDetail['hospitalId'],
            'starttime': timeDetail['starttime'],
            'endtime': timeDetail['endtime'],
            'unit_code': dateDetail['unitCode'],
            'unit_name': dateDetail['unitName'].encode('utf-8'),
            'doctor_name': self.doctor['name'].encode('utf-8'),
            'doctor_code': self.doctor['code'],
            'reserve_date': dateDetail['date'],
            'charge_type_name': dateDetail['chargeTypeName'].encode('utf-8'),
            'apm': u'上午'.encode('utf-8') if dateDetail['ampm'] == 'a' else u'下午'.encode('utf-8'),
            'clinic_fee': dateDetail['clinicFee'],
            'charge_type': dateDetail['chargeType']
        }
        param = urlencode(data)
        # print param
        confirmPage = confirmPage + param
        # print order_url
        headers = dict()
        headers["Referer"] = self.doctor['url']
        self.headers.update(headers)
        # 预约信息确认的页面
        response = self.session.get(confirmPage, headers=self.headers)
        logging.info(u"确认信息页面状态：%s， URL: %s" % (str(response.status_code), response.url))
        if response.status_code != 200:
            logging.error(u"确认预约信息失败\n" + response.text)
            sys.exit(0)
        self.headers.update(Referer=response.url)

        def parseParams(htmlContent):
            '''
            解析确认页面，提取参数
            :param htmlContent:
            :return:
            '''
            result = re.findall(r"\$\('#preregister-submit'\).click\(function\(\)\{(.*)\$\.ajax", htmlContent, re.S)
            params = {}
            params['callback'] = 'submitcallback'
            for i in result:
                i = i.replace('var ', '')
                for j in i.split(';'):
                    if j.strip():
                        items = j.split('=', 1)
                        key = items[0].strip()
                        value = items[1].strip().replace('\'', '').replace('\"', '')
                        params[key] = value.encode('utf-8')
            params['_'] = format(time.time() * 1000, '.0f')
            return params

        # print response.text
        def confirmSubmit(params):
            '''
            确认提交，把预约信息提交给服务器，预约的最后一步
            :param params:
            :return:
            '''
            baseUrl = "http://new.sdfyy.cn/preregister"
            ajaxUrl = params.pop('getAjaxDetail')[1:]
            targetURL = baseUrl + ajaxUrl
            # 提交预约信息
            orderResponse = self.session.get(targetURL, params=params, headers=self.headers)
            logging.info(u"提交预约信息的状态：%s, URL: %s" % (str(orderResponse.status_code), orderResponse.url))
            if orderResponse.status_code == 200:
                # response message
                message = orderResponse.text
                message = message[message.find('(') + 1:-1]
                # print message
                responseJson = json.loads(message)
                # print responseJson['code'], responseJson['msg']
                if responseJson['code'] == 201:
                    # 预约成功，发送短信
                    self.sendSMS(phoneNo=responseJson['tel']['mobileno'], message=responseJson['tel']['msg'])
                    return True
                elif responseJson['code'] == 500:
                    logging.error(u"服务器端错误,请在浏览器端重试: %s" % (responseJson['msg'],))
                    return False
                else:
                    logging.error(u"提交预约信息失败\n" + responseJson)
                    return False
            else:
                logging.error(u"提交预约信息失败\n" + orderResponse.text)
                return False

        params = parseParams(response.text)
        return confirmSubmit(params)

    def sendSMS(self, phoneNo=u"手机号", message=u"短信内容"):
        '''发送短信'''
        smsUrl = "http://new.sdfyy.cn/preregister/localhost/sdfyy/index.php?s=/Appointment/sendSms"
        headers = {"X-Requested-With": "XMLHttpRequest"}
        self.headers.update(headers)
        # "msg": "您预约2018-11-15核医学科（甲亢门诊）桑士标医生的13号，密码856564。于08:00--08:45凭医保卡或身份证至自助机（吴江医保至二楼5-7号窗口）取号，过时作废。附一院十梓街院区（十梓街188号）"
        data = {
            "mobileno": phoneNo,
            "msg": message
        }
        sendSMSResponse = self.session.post(smsUrl, data=data, headers=self.headers)
        logging.info(u"发送短信的状态：%s, URL: %s" % (str(sendSMSResponse.status_code), sendSMSResponse.url))
        logging.info(sendSMSResponse.content)
        self.headers.pop("X-Requested-With")

    def order(self):
        if self.__login():
            self.__orderDoctor()
            self.__logout()


class SZ12320(object):
    '''苏州12320医疗预约平台'''

    def __init__(self, user=None, doctor=None):
        self.user = user
        self.doctor = doctor
        self.session = requests.Session()
        headers = dict()
        headers[
            "User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:63.0) Gecko/20100101 Firefox/63.0"
        headers["Host"] = "www.jssz12320.cn:8080"
        headers["Origin"] = "http://www.jssz12320.cn:8080"
        self.headers = headers

    def step1(self):
        step01Url = "http://www.jssz12320.cn:8080/hrs/step01"
        response = self.session.get(step01Url, headers=self.headers)
        # print "step01_start " + str(response.status_code) + " " + response.url
        logging.info("step01_start " + str(response.status_code) + " " + response.url)
        self.isDenyed(response.url)

        queryIdNameUrl = "http://www.jssz12320.cn:8080/hrs/query_by_id_name"
        self.headers['Referer'] = "http://www.jssz12320.cn:8080/hrs/step01"
        self.headers['X-Requested-With'] = "XMLHttpRequest"

        data = {
            'id': self.user['id'],
            'name': self.user['name'],
            'birthday': '',
            'time': time.strftime("%a %b %d %Y %H:%M:%S GMT+0800 (China Standard Time)", time.localtime())
        }
        # print data
        response = self.session.post(queryIdNameUrl, data=data, headers=self.headers)
        # print "step01_query_by_id_name " + str(response.status_code) + " " + response.url
        # print "query_by_id_name result ==> " + response.content
        logging.info("step01_query_by_id_name " + str(response.status_code) + " " + response.url)
        logging.info("query_by_id_name result ==> " + unicode(response.text))
        if response.content.find('true') > -1:
            msg = json.loads(response.content)
            self.user['phone'] = msg['phone_hide']
            self.user['type'] = msg['type']

        self.isDenyed(response.url)
        self.session.cookies.update(response.cookies)

        self.headers.pop("X-Requested-With")
        self.headers['Upgrade-Insecure-Requests'] = '1'
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"
        self.headers['Accept'] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        self.headers['Pragma'] = "no-cache"
        self.headers['Cache-Control'] = 'no-cache'
        toStep2 = "http://www.jssz12320.cn:8080/hrs/verify"

        verifyData = {
            'id': self.user['id'],
            'name': self.user['name'],
            'phone': self.user['phone'][0:3] + "****" + self.user['phone'][7:],
            'medicalType': self.user['type']
        }
        response = self.session.post(toStep2, data=verifyData, headers=self.headers)
        # print "step01_verify " + str(response.status_code) + " " + response.url
        logging.info("step01_verify " + str(response.status_code) + " " + response.url)
        self.isDenyed(response.url)

    def step2(self):
        hospitalCode = hospitals.hospitals.get(self.doctor['hospital'])
        url = "http://www.jssz12320.cn:8080/hrs/step02_post_action?hospitalId=" + str(hospitalCode)
        response = self.session.get(url, headers=self.headers)
        # print "step02_post_action " + str(response.status_code) + " " + response.url
        logging.info("step02_post_action " + str(response.status_code) + " " + response.url)
        self.isDenyed(response.url)

    def step3(self):
        doctorScheduleURL = "http://www.jssz12320.cn:8080/hrs/load_doc_schedule"
        self.headers['X-Requested-With'] = "XMLHttpRequest"
        self.headers['Referer'] = 'http://www.jssz12320.cn:8080/hrs/step03.action'
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        form = {
            'deptName': '',
            'docName': self.doctor['name'],
            'hospName': self.doctor['hospital'],
            'page.pageNum': 1,
            'regType': 2,
            'weekth': 1
        }
        response = self.session.post(doctorScheduleURL, data=form, headers=self.headers)
        # print "step03_load_doc_schedule " + str(response.status_code) + " " + response.url
        logging.info("step03_load_doc_schedule " + str(response.status_code) + " " + response.url)
        self.isDenyed(response.url)

        def parseDateSchedule(content):
            result = re.findall(r".*onclick=\"loadTimeList\(this,(.*)\)\".*", content, re.M)
            dateList = []
            if result:
                for e in result:
                    data = {
                        "hospName": None, "departName": None, "doctorName": None, "workType": None, "workDate": None,
                        "clinicFee": None, "registerFee": None, "expertFee": None, "remark": None
                    }
                    values = e.split(',')
                    data["hospName"] = values[0].replace('\'', '')
                    data['departName'] = values[1].replace('\'', '')
                    data['doctorName'] = values[2].replace('\'', '')
                    data['workType'] = values[3].replace('\'', '')
                    data['workDate'] = values[4].replace('\'', '')
                    data['clinicFee'] = values[5].replace('\'', '')
                    data['registerFee'] = values[6].replace('\'', '')
                    data['expertFee'] = values[7].replace('\'', '')
                    data['remark'] = values[8].replace('\'', '')
                    dateList.append(data)

            if dateList:
                dateList.sort(key=lambda x: x["workDate"])
            return dateList

        def parseTimeSchedule(content):
            def formatDate(dateStr):
                if dateStr and dateStr.endswith('CST 1970'):
                    b = time.strptime(dateStr, '%a %b %d %H:%M:%S CST %Y')
                    c = time.strftime('%Y-%m-%d %H:%M', b)
                    return c
                elif dateStr and dateStr.startswith('1970'):
                    return dateStr
                else:
                    return dateStr

            result = re.findall(r".*onclick=\"toRegister\((.*)\)\".*", content, re.M)
            timeList = []
            if result:
                for e in result:
                    data = {}
                    values = e.split(',')
                    data["hospName"] = values[0].replace('\'', '')
                    data['depName'] = values[1].replace('\'', '')
                    data['doctorName'] = values[2].replace('\'', '')
                    data['workDate'] = values[3].replace('\'', '')
                    data['workType'] = values[4].replace('\'', '')
                    data['startTime'] = formatDate(values[5].replace('\'', ''))
                    data['endTime'] = formatDate(values[6].replace('\'', ''))
                    timeList.append(data)

            if timeList:
                timeList.sort(key=lambda x: x["startTime"])
            return timeList

        def orderTheDoctor(timeDic):
            url = "http://www.jssz12320.cn:8080/hrs/step03_post_action"
            response = self.session.post(url, data=timeDic, headers=self.headers)
            # print "step03_post_action " + str(response.status_code) + " " + response.url + " " + timeDic['startTime']
            logging.info(
                "step03_post_action " + str(response.status_code) + " " + response.url + " " + timeDic['startTime'])
            if response.status_code == 200:
                if response.url == "http://www.jssz12320.cn:8080/hrs/step04.action":
                    self.step4(response.content)
                    return True
            else:
                return False

        def getRegisterTimeList(params):
            registerTimeUrl = "http://www.jssz12320.cn:8080/hrs/register_loadTimeList"
            data = {}
            data['t'] = 0
            data['methodType'] = 0
            data.update(params)
            response = self.session.post(registerTimeUrl, data=data, headers=self.headers)
            timeList = []
            # print "step03 register_loadTimeList " + str(response.status_code) + " " + response.url + " " + params[
            #     'workDate']
            logging.info(
                "step03 register_loadTimeList " + str(response.status_code) + " " + response.url + " " + params[
                    'workDate'])
            if response.status_code == 200:
                # print response.content
                timeList = parseTimeSchedule(response.content)
            return timeList

        dateList = parseDateSchedule(response.content)
        useSecondWeek = False
        if not dateList:
            # print "the first week dateList is empty, now search the second week ......"
            logging.warning("the first week dateList is empty, now search the second week ......")
            useSecondWeek = True
            form['weekth'] = 2
            response = self.session.post(doctorScheduleURL, data=form, headers=self.headers)
            # print "step03_load_doc_schedule again " + str(response.status_code) + " " + response.url
            logging.info("step03_load_doc_schedule again " + str(response.status_code) + " " + response.url)
            self.isDenyed(response.url)
            dateList = parseDateSchedule(response.content)
        if dateList:
            for eachDate in dateList:
                timeList = getRegisterTimeList(eachDate)
                for eachTime in timeList:
                    ordered = orderTheDoctor(eachTime)
                    if ordered:
                        sys.exit(0)
        else:
            # print "there is no number to order at the {:d}th week".format(form['weekth'])
            logging.warning("there is no number to order at the {:d}th week".format(form['weekth']))

        if useSecondWeek == False:
            # print "first week has no date to order, now search the second week ......"
            logging.info("first week has no date to order, now search the second week ......")
            form['weekth'] = 2
            response = self.session.post(doctorScheduleURL, data=form, headers=self.headers)
            # print "step03_load_doc_schedule again  " + str(response.status_code) + " " + response.url
            logging.info("step03_load_doc_schedule again  " + str(response.status_code) + " " + response.url)
            self.isDenyed(response.url)
            dateList = parseDateSchedule(response.content)
            for eachDate in dateList:
                timeList = getRegisterTimeList(eachDate)
                for eachTime in timeList:
                    ordered = orderTheDoctor(eachTime)
                    if ordered:
                        sys.exit(0)
            # print "there is no number to order at the {:d}th week".format(form['weekth'])
            logging.info("there is no number to order at the {:d}th week".format(form['weekth']))

    def step4(self, content):
        def getCheckValue(content):
            result = re.findall(r".*var checkvalue=eval\(\'(.*)\'\);.*", content, re.M)
            if result:
                # print 'checkvalue is ' + result[0]
                logging.info('checkvalue is ' + result[0])
                return eval(result[0])

        url = "http://www.jssz12320.cn:8080/hrs/step04_post_action"
        checkvalue = getCheckValue(content)
        if not checkvalue:
            # print "step04 get checkvalue error"
            logging.error("step04 get checkvalue error")
            sys.exit(0)

        # 最终的确定预约
        # response = self.session.post(url, data={'checkvalue': checkvalue, 't': format(time.time() * 1000, '.0f')},
        #                              headers=self.headers)
        # print "step04_post_action " + str(response.status_code) + " " + response.url
        # print response.content

    def isDenyed(self, url):
        if url.find('acc_dny') > -1:
            print "access deny : " + url
            sys.exit(0)

    def order(self):
        self.step1()
        self.step2()
        self.step3()


if __name__ == "__main__":
    print u'开始执行。。。。。。'
    # sz12320user = {
    #     'id': u'身份证号',
    #     'name': u'姓名',
    #     'type': u'市民卡',  # 自费，市民卡
    #     'phone': u'手机号'
    # }
    # sz12320doctor = {
    #     'name': u"医生姓名",
    #     'hospital': u'医院名字',
    #     'date': u'date',  # todo 支持选日期和时间段
    #     'time': u'09-10' # 08-09 代表 8 点至 9 点
    # }
    # sz = SZ12320(user=sz12320user, doctor=sz12320doctor)
    # sz.order()

    sduser = {
        'id': '身份证号',
        'name': u'姓名',
        'password': '密码',
        'date': '2019-07-11'
    }

    sddoctor = {
        'name': u'医生姓名'
    }

    sd = SuDaHospital(user=sduser, doctor=sddoctor)
    sd.order()
