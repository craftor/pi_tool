import socket
import uuid
import netifaces

class udp_cmder(object):

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
        """
        self.ss.sendto(cmd.encode('utf-8'), (host, self.PORT))

    def broadcast(self):
        cmd = self.gen_broadcast_cmd()
        self.ss.sendto(cmd.encode('utf-8'), ('<broadcast>', self.PORT))

    def test(self):
        """
        运行
        """
        # cmd = self.gen_ip_change_cmd('b8:27:eb:80:a9:d1', '192.168.1.80', '255.255.255.0', '192.168.1.1')
        self.get_ip_mask_gateway()
        # cmd = self.gen_broadcast_cmd(mac, )
        # self.send_cmd(cmd)

if __name__ == "__main__":
    sender = udp_cmder(1060)
    sender.broadcast()