
import time
import threading
import socket
import uuid
import netifaces
import socket
import shutil
import uuid
import os

class udp_receiver(object):

    def __init__(self, port):
        """
        初始化
        """
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.ss.bind(('', port))
        print('Listening for broadcast at ', self.ss.getsockname())

    def get_mac_address(self):
        """
        获取mac地址
        """
        mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
        return ":".join([mac[e:e+2] for e in range(0,11,2)])

    def gen_target_file(self, target_ip, target_mask, target_gateway):
        """
        生成目标配置文件
        """
        msg = "auto eth0 \n"
        msg += "iface eth0 inet static \n"
        msg += "address " + (target_ip) + "\n"
        msg += "netmask " + (target_mask) + "\n"
        msg += "gateway " + (target_gateway) + "\n"
        print(msg)
        with open('target.txt', 'wt') as f:
            f.write(msg)

    def msg_process(self, msg):
        """
        处理信息
        """
        mylist = str(msg).split('|')
        # print(mylist)
        mymac = self.get_mac_address()
        if len(mylist) >= 3:
            if (mylist[0] == 'change_ip') and (mylist[1] == mymac):
                print("Change Ip Command Received")
                self.change_ip(str(mylist[2]), str(mylist[3]), str(mylist[4]))
                os.system("reboot")

    def change_ip(self, dest_ip, dest_mask, dest_gateway):
        """
        修改IP操作
        """
        self.gen_target_file(dest_ip, dest_mask, dest_gateway)
        shutil.copy("target.txt", "/etc/network/interfaces")

    def run(self):
        """
        运行
        """
        while True:
            data, address = self.ss.recvfrom(65535)
            print('Server received from {}:{}'.format(address, data.decode('utf-8')))
            self.msg_process(data.decode('utf-8'))


class udp_sender(object):
    
    def __init__(self, port):
        """
        初始化
        """
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ss.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.PORT = port
        self.network = '<broadcast>'

    def get_ip_mask_gateway(self):
        """
        获取本机mac, ip, mask , gateway
        """
        routingGateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
        routingNicName = netifaces.gateways()['default'][netifaces.AF_INET][1]

        for interface in netifaces.interfaces():
            if interface == routingNicName:
                # print netifaces.ifaddresses(interface)
                routingNicMacAddr = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
                try:
                    routingIPAddr = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                    # TODO(Guodong Ding) Note: On Windows, netmask maybe give a wrong result in 'netifaces' module.
                    routingIPNetmask = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['netmask']
                except KeyError:
                    pass

        ip_list = [routingNicMacAddr, routingIPAddr, routingIPNetmask, routingGateway]
        # print(ip_list)
        return ip_list

    def get_mac_address(self):
        """
        获取mac地址
        """
        mac=uuid.UUID(int = uuid.getnode()).hex[-12:] 
        return ":".join([mac[e:e+2] for e in range(0,11,2)])

    def gen_ip_change_cmd(self, my_list):
        """
        生成改ip的命令包
        """
        cmd_list = []
        cmd_list.append('change_ip')
        cmd_list.append(my_list[0])
        cmd_list.append(my_list[1])
        cmd_list.append(my_list[2])
        cmd_list.append(my_list[3])
        return self.list2str(cmd_list)

    def gen_broadcast_cmd(self):
        """
        生成改广播自己ip的命令包
        """
        ip_list = self.get_ip_mask_gateway()
        cmd_list = []
        cmd_list.append('my_ip')
        cmd_list.append(ip_list[0])
        cmd_list.append(ip_list[1])
        cmd_list.append(ip_list[2])
        cmd_list.append(ip_list[3])
        return self.list2str(cmd_list)

    def list2str(self, cmd_list):
        """
        List 转 Str
        """
        str = ""
        for each in cmd_list:
            str += each + "|"
        return str

    def send_cmd(self, host, cmd):
        """
        发送命令
        注意：这里发udp包也指定了host，因为如果电脑上有多个网卡的时候，使用<broadcast>树莓派会收不到udp命令包
        """
        self.ss.sendto(cmd.encode('utf-8'), (host, self.PORT))

    def broadcast(self):
        """
        广播自己的信息
        """
        cmd = self.gen_broadcast_cmd()
        self.ss.sendto(cmd.encode('utf-8'), ('<broadcast>', self.PORT))


class broadcastThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.cmder = udp_sender(1060)

    def run(self):
        while True:
            self.cmder.broadcast()
            time.sleep(5)

class receiverThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.receiver = udp_receiver(1060)

    def run(self):
        self.receiver.run()


if __name__ == "__main__":

    t1 = broadcastThread()
    t2 = receiverThread()

    t1.start()
    t2.start()