
import socket
import shutil
import uuid
import os

class udp_listener(object):

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

if __name__ == "__main__":
    server = udp_listener(1060)
    server.run()