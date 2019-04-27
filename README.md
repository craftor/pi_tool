
# 树莓派改ip小工具

1. Pi端，两个线程
    * 线程一，每5秒种发udp广播一下自己的mac、ip、mask、gateway等
    * 线程二，等待上位机发的命令
2. PC端，使用PyQt5写的, eric6设计的界面
3. package.cmd 是windows平台自动打包的脚本
4. 仅支持python3, 依赖库：
    * pi端: netifaces
    * pc端：pyinstaller, pyqt5, pyqt5-tools