# -*- coding: utf-8 -*-
# @Time    : 2018/11/13 10:32
# @Software: PyCharm

import os
import sys
import logging
import logging.handlers


LOG_LEVEL = "info"
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s] [%(funcName)s] [line:%(lineno)d] %(message)s"
DATA_LOG_FORMAT = "%Y/%m/%d %H:%M:%S"


class MyLogger(object):
    def __init__(self, log_name="mylogger", log_level=LOG_LEVEL, log_dir="logs", show_console=False):
        self.logObject = logging.getLogger()
        log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), log_dir)

        if not os.path.exists(log_dir):
            try:
                os.mkdir(log_dir)
            except Exception as e:
                sys.stderr.write("Can not create " + log_dir + ", please check your access right," + str(e))
                sys.exit(0)
        else:
            pass

        log_file = os.path.join(log_dir, log_name) + ".log"
        self.__set_level(log_level)

        # 将LOG文件按照每天分成不同的文件
        file_handler = logging.handlers.TimedRotatingFileHandler(log_file, 'midnight', interval=1, backupCount=10,
                                                                 encoding="UTF-8")
        file_handler.suffix = "%Y%m%d.log"
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATA_LOG_FORMAT)
        file_handler.setFormatter(formatter)
        self.logObject.addHandler(file_handler)

        # # 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
        if show_console:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter(LOG_FORMAT, datefmt="%H:%M:%S")
            console.setFormatter(formatter)
            self.logObject.addHandler(console)

    def __set_level(self, log_level):
        if log_level == "warning":
            self.logObject.setLevel(logging.WARNING)
        elif log_level == "debug":
            self.logObject.setLevel(logging.DEBUG)
        elif log_level == "error":
            self.logObject.setLevel(logging.ERROR)
        elif log_level == "critical":
            self.logObject.setLevel(logging.CRITICAL)
        else:
            self.logObject.setLevel(logging.INFO)

# if __name__ == '__main__':
#     LOGGING("test")
#     logging.info("info")
#     logging.warning("warning")
