# -*- coding: utf-8 -*-

"""
Module implementing Dialog.
"""
import sys
import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtWidgets import QMainWindow, QAction, qApp 
from PyQt5.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QTableWidget,QFrame,QAbstractItemView, QTableWidgetItem, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread, pyqtSignal

from Ui_main import Ui_Dialog

from pi_udp import udp_sender, udp_receiver

import subprocess
import datetime
import time
import socket
import threading
import uuid

VERSION = 3.1

# 更新ip的线程
class RBCThread(QThread):
    finishSignal = pyqtSignal(list)
    def __init__(self, parent=None):
        super(RBCThread, self).__init__(parent)

        # Socket Receiver
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.ss.bind(('', 1060))
        print('Listening for broadcast at ' + str(self.ss.getsockname()))

    def check_pi(self, mac):
        """
        判断一台主机是否为Pi
        """
        mac_list = str(mac).split(':')
        if mac_list[0] == 'B8' or mac_list[0] == 'b8':
            print("Find a Pi")
            return True
        else:
            return False

    def get_mac_address(self):
        """
        获取mac地址
        """
        mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
        return ":".join([mac[e:e+2] for e in range(0,11,2)])

    def msg_process(self, msg):
        """
        处理信息
        """
        my_list = str(msg).split('|')
        # print(mylist)
        mymac = self.get_mac_address()
        if len(my_list) >= 5:
            if (my_list[0] == 'my_ip') and self.check_pi(my_list[1]):
                self.finishSignal.emit(my_list[1:])

    def run(self):
        while True:
            data, address = self.ss.recvfrom(65535)
            str_data = data.decode('utf-8')
            print('Server received from {}:{}'.format(address, str_data))
            self.msg_process(str_data)

class Dialog(QDialog, Ui_Dialog):
    """
    Class documentation goes here.
    """

    def __init__(self, parent=None):
        """
        """
        super(Dialog, self).__init__(parent)
        self.setupUi(self)

        # 版本号
        title = "树莓派改IP小工具 v" + str(VERSION)
        self.setWindowTitle(title)

        # 初始化表格
        self.init_table()
        self.lines = []

        # 侦听广播
        self.tk3 = RBCThread()
        self.tk3.finishSignal.connect(self.add_line)
        self.tk3.start()

        # Up and Down
        self.udp_sender = udp_sender(1060)
        self.log_print("正在扫描设备...")

        self.lines = []

    def log_print(self, str):
        """
        带时间日期的打印信息输出
        """
        now = datetime.datetime.now()
        otherStyleTime = now.strftime("%Y-%m-%d %H:%M:%S")
        msg = otherStyleTime + " - " + str
        self.textEdit.append(msg)

    def init_table(self):
        """
        初始化Table
        """
        self.tableWidget.setColumnCount(5)##设置表格一共有五列
        self.tableWidget.setHorizontalHeaderLabels(['mac', 'ip', 'mask', 'gateway', 'update',])#设置表头文字
        self.tableWidget.horizontalHeader().setSectionsClickable(False) #可以禁止点击表头的列
        # self.tableWidget.horizontalHeader().setStretchLastSection(True)

    def check_pi(self, mac):
        """
        判断一台主机是否为Pi
        """
        mac_list = str(mac).split(':')
        # print(mac_list)
        if mac_list[0] == 'B8' or mac_list == 'b8':
            return False
        else:
            print("Find a Pi")
            return True

    def remove_line(self, i):
        """
        删除一行
        """
        self.tableWidget.removeRow(i)

    def add_line(self, ip_list):
        """
        增加一行
        """
        for i in range(self.tableWidget.rowCount()):
            # 已经有了
            if self.tableWidget.item(i, 0).text() == ip_list[0]:
                return

        self.log_print("发现新的设备:" + str(ip_list[0]))
        row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(row + 1)
        self.tableWidget.setItem(row,0,QTableWidgetItem(ip_list[0]))
        self.tableWidget.setItem(row,1,QTableWidgetItem(ip_list[1]))
        self.tableWidget.setItem(row,2,QTableWidgetItem(ip_list[2]))
        self.tableWidget.setItem(row,3,QTableWidgetItem(ip_list[3]))

        # button = QPushButton(
        #     self.tr('更新'),
        #     self.parent(),
        #     clicked=lambda: self.ip_change(ip_list, row)
        #     )
        check = QCheckBox()

        h = QHBoxLayout()
        h.setAlignment(Qt.AlignCenter)
        h.addWidget(check)
        w = QWidget()
        w.setLayout(h)
        
        self.tableWidget.setCellWidget(row, 4, check)
        self.tableWidget.resizeRowsToContents()
        # self.tableWidget.resizeColumnsToContents()

        self.lines.append(ip_list)

    def ip_change(self, my_list, row):
        """
        执行更新IP的命令
        """
        new_list = [my_list[0], \
                    self.tableWidget.item(row,1).text(), \
                    self.tableWidget.item(row,2).text(), \
                    self.tableWidget.item(row,3).text()]
        cmd = self.udp_sender.gen_ip_change_cmd(new_list)
        # print(cmd)
        self.udp_sender.send_cmd(my_list[1], cmd)
        # self.remove_line(row)
        self.log_print("更新 ({}){} 至 {}，重启中...".format(my_list[0], my_list[1], new_list[1]))

    def refresh(self):
        """
        刷新
        """
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.lines = []

    @pyqtSlot()
    def on_pushButton_ClearLog_clicked(self):
        """
        清空日志
        """
        self.textEdit.setText("")

    @pyqtSlot()
    def on_pushButton_Refresh_clicked(self):
        """
        刷新目录
        """
        self.refresh()

    @pyqtSlot()
    def on_pushButton_UpdateAll_clicked(self):
        """
        全部更新
        """
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 4).isChecked():
                self.ip_change(self.lines[row], row)
                # self.log_print("")
        self.refresh()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Dialog()
    main.show()
    sys.exit(app.exec_())
    