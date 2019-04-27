import nmap
import sys
import os

import socket
import json

class NmapScan():

    def __init__(self):
        """
        增加nmap运行目录
        """
        current_path = os.getcwd() + "\\nmap-7.70"
        os.environ["PATH"] += ";" + current_path

        # 原始IP
        self.user = "pi"
        self.passwd = "passw0rd"

    def ssh_login(self, host):
        """
        SSH 登录
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(str(host), username=str(self.user), password=str(self.passwd))
            return ssh
        except Exception:
            return None

    def sudo_copy(self, host, src, dst):
        """
        SUDO权限复制文件
        """
        ssh = self.ssh_login(host, self.user, self.passwd)
        if ssh is None:
            return False
        else:
            cmd = "sudo cp " + str(src) + " " + str(dst)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.readlines())
            return True

    def sudo_reboot(self, host):
        """
        重启
        """
        ssh = self.ssh_login(host, self.user, self.passwd)
        if ssh is None:
            return False
        else:
            cmd = "sudo reboot"
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=1)
            # print(stdout.readlines())
            return True

    def sftp_login(self, host):
        """
        SFTP 登录
        """
        try:
            sf = paramiko.Transport(host)
            sf.connect(username=self.user, password=self.passwd)
            print("sftp login success")
            return sf
        except Exception:
            print("sftp login failed")
            return None

    def sftp_upload(self, host, local, remote):
        """
        SFTP 上传
        """
        sf = self.sftp_login(host)
        if sf is None:
            return False
        sftp = paramiko.SFTPClient.from_transport(sf)
        try:
            sftp.put(local, remote)  # 上传文件
        except Exception:
            print('upload failed')
        sf.close()
        return True

    def sftp_download(self, host, local, remote):
        """
        SFTP 下载
        """
        sf = self.sftp_login(host, self.user, self.passwd)
        if sf is None:
            return
        sftp = paramiko.SFTPClient.from_transport(sf)
        try:
            sftp.get(remote, local)  # 下载文件
        except Exception:
            print('download failed')
        sf.close()
        return True

    def gen_target_file(self, target_ip, target_mask, target_gatway):
        """
        生成目标配置文件
        """
        msg = "auto eth0 \n"
        msg += "iface eth0 inet static \n"
        msg += "address " + (target_ip) + "\n"
        msg += "netmask " + (target_mask) + "\n"
        msg += "gateway " + (target_gatway) + "\n"
        with open('target.txt', 'wt') as f:
            f.write(msg)

    def update_all(self, ip_list):
        """
        全部更新
        """
        for row in ip_list:
            self.update_ip(row[0], row[1])
            print("Updating " + str(row[0]) + " ---> " + str(row[1]))

    def recovery(self, host):
        """
        还原网络设置
        """
        if self.sftp_upload(host, "backup.txt", "/home/pi/backup.txt"):
            self.sudo_copy(host, "/home/pi/backup.txt", "/etc/network/interfaces")
            self.log_print("还原完成")
        else:
            self.log_print("还原失败")

    def backup(self):
        """
        备份网络设置
        """
        if self.sftp_download(host, "backup.txt", "/etc/network/interfaces"):
            self.log_print("备份完成")
        else:
            self.log_print("备份失败")

    def ping(self):
        """
        Ping
        """
        cmd = "ping " + str(self.org_ip)
        print(cmd)
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        result_lines = p.stdout.readlines()
        msg = ""
        for line in result_lines:
            output = line.decode('cp936')
            msg += output
            print(output)
        self.textEdit.append(msg)

    def update_ip(self, org_ip, dst_ip):
        """
        更新IP地址
        """
        self.gen_target_file(dst_ip)
        if self.sftp_upload(org_ip, "target.txt", "/home/pi/target.txt"):
            self.sudo_copy(org_ip, "/home/pi/target.txt", "/etc/network/interfaces")
            self.sudo_reboot(org_ip)
            print("update ip success")
            return True
        else:
            print("update ip failed")
            return False

    def get_ip(self):
        """
        获取本机IP
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    
    def get_network_prefix(self):
        """
        组装成网段，类如 192.168.1.0/24
        """
        ip = self.get_ip()
        list = str(ip).split('.')
        result = list[0] + '.' + list[1] + '.' + list[2] + '.0/24'
        # print(result)
        return result

    def check_pi(self, mac, servername):
        """
        判断一台主机是否为Pi
        """
        mac_list = str(mac).split(':')
        name_list = str(servername).split()
        if mac_list[0] != 'B8':
            return False
        if name_list[0] != "Raspberry":
            return False
        return True

    def get_all_host(self):
        """
        扫描所有主机
        """
        print("Start to Scan")
        result = self.nmap(self.get_network_prefix(), '-sP')
        # print(result)
        all_list = []
        for row in result['scan']:
            vendor = result['scan'][row]['vendor']
            for mac in vendor:
                tmp_list = []
                tmp_list.append(row)
                tmp_list.append(mac)
                tmp_list.append(vendor[mac])
                all_list.append(tmp_list)
        print(all_list)
        return all_list

    def get_pi_list(self):
        """
        获取局域网内所有树莓派的IP地址
        """
        print("Start to Scan")
        result = self.nmap(self.get_network_prefix(), '-sP')
        # print(result)
        pi_list = []
        for row in result['scan']:
            vendor = result['scan'][row]['vendor']
            for mac in vendor:
                tmp_list = []
                if self.check_pi(mac, vendor[mac]) :
                    tmp_list.append(row)
                    tmp_list.append(mac)
                    tmp_list.append(vendor[mac])
                    pi_list.append(tmp_list)
        # print(pi_list)
        return pi_list

    def nmap(self, network_prefix, arguments):
        """
        nmap通用扫描
        """
        nm = nmap.PortScanner()
        scan_raw_result = nm.scan(hosts=network_prefix, arguments=arguments)
        return scan_raw_result

if __name__ == '__main__':
    test = NmapScan()
    test.get_all_host()
