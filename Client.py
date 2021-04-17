import socket
import json
import threading
import copy
import logging
import time
import wx
from ChattingRoomModel import *
from AudioHelper import recordwav, playwav


class Client(object):

    def run(self):
        self.sendThread = threading.Thread(target=self.handleRequest)
        self.recvThread = threading.Thread(target=self.handleReceive)
        self.sendThread.start()
        self.recvThread.start()

    def initEnvironment(self, addr, port, username):
        """初始化环境变量
        """
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((addr, port))

        self.user = username
        # 默认为下线状态
        self.status = ClientStatus.offline
        # ui的回调函数
        self.callback = None

    def __timestampToString(self, timestamp):
        t = time.localtime(timestamp)
        w = time.strftime("%Y-%m-%d %H:%M:%S", t)
        return w

    def sendMessage(self, action, msg=None):
        sendMsg = copy.deepcopy(sendMessageModel)
        sendMsg['action'] = action.name
        sendMsg['user'] = self.user
        if msg:
            sendMsg['data'] = {
                'username': self.user,
                'time': time.time(),
                'msg': msg
            }
        # client.send(json.dumps(sendMsg).encode())
        sendWithCache(self.client, json.dumps(sendMsg))

    def login(self):
        self.sendMessage(ClientAction.login)
        self.status = ClientStatus.online

    def logout(self):
        self.sendMessage(ClientAction.logout)
        self.status = ClientStatus.offline

    def handleMessage(self, msgs):
        import base64
        for msg in msgs:
            _type = msg['type']
            if _type == MessageType.text.name:
                print("{} {}:\n{}".format(msg['from'], self.__timestampToString(
                    msg['time']), msg['data']))
            elif _type == MessageType.file.name:
                import os
                filePath = 'UserData/Download'
                if not os.path.exists(filePath):
                    os.makedirs(filePath)
                url = os.path.join(filePath, msg['filename'])
                with open(url, 'wb') as f:
                    _data = msg['data']
                    _data += '=' * (-len(_data) % 4)
                    _data = base64.urlsafe_b64decode(_data.encode())
                    f.write(_data)
                    print("{} {}:\n发送了文件:{}, 存放至{}".format(msg['from'], self.__timestampToString(msg['time']), msg['filename'], url))
            elif _type == MessageType.mp3.name:
                import os
                filePath = 'UserData/Download'
                if not os.path.exists(filePath):
                    os.makedirs(filePath)
                url = os.path.join(filePath, msg['filename'])
                with open(url, 'wb') as f:
                    _data = msg['data']
                    _data += '=' * (-len(_data) % 4)
                    _data = base64.urlsafe_b64decode(_data.encode())
                    f.write(_data)
                    print("{} {}:\n发送了语音:{}, 存放至{}".format(msg['from'], self.__timestampToString(msg['time']), msg['filename'], url))
                playwav(url)

    def handleReceive(self):
        while True:
            if self.status == ClientStatus.offline:
                continue
            else:
                try:
                    # retMsg = client.recv(1024)
                    retMsg = recvWithCache(self.client, dict())[0]
                    retMsg = json.loads(retMsg)
                    # 对消息状态进行判断
                    if retMsg['status'] == 0:
                        logging.info('请求失败', retMsg['msg'])
                    else:
                        logging.info('请求成功')
                        _action = retMsg['action']
                        _msgs = retMsg['data']['msgs']
                        _onlineUsers = retMsg['data']['onlineUsers']

                        if _action == ServerAction.info.name:
                            print(retMsg['msg'])
                        elif _action == ServerAction.loginSuccess.name:
                            logging.info('欢迎您 {}\n当前在线用户: {}'.format(self.user, _onlineUsers))
                        elif _action == ServerAction.logoutSuccess.name:
                            logging.info('已登出')
                            self.status = ClientStatus.offline
                            import os
                            os._exit(0)
                        elif _action == ServerAction.newMessage.name:
                            logging.info('新信息')
                            self.handleMessage(_msgs)

                except Exception as err:
                    logging.error('接收错误: %s', err)

    def makeMsg(self, type, dataStr, to='', filename=''):
        msg = copy.deepcopy(messageModel)
        msg['from'] = self.user
        msg['to'] = to
        msg['time'] = time.time()
        msg['type'] = type.name
        msg['data'] = dataStr
        msg['filename'] = filename
        return msg

    # cli上判断动作的函数
    def handleRequest(self):
        import os
        import base64
        while True:
            op = input(
                '请输入要进行的操作: \n1: send text\n2: send file\n3: send voice\n4: exit\n')
            if op not in list(map(str, [1, 2, 3, 4])):
                print('无效操作')
                continue
            elif op == '1':
                text = input('发一句友善的话: ')
                self.sendMessage(ClientAction.sendMsg, self.makeMsg(MessageType.text, text))
            elif op == '2':
                url = input('输入文件路径: ')
                # 使用绝对路径来代替可能输入的相对路径
                url = os.path.abspath(url)
                fileName = url.split('/')[-1]
                print(fileName)
                try:
                    with open(url, 'rb') as f:
                        fileData = f.read()
                        fileData = base64.urlsafe_b64encode(fileData).decode()
                        self.sendMessage(ClientAction.sendMsg, self.makeMsg(MessageType.file, fileData, filename=fileName))
                except Exception as err:
                    print('文件读取错误%s'%err)
            elif op == '3':
                t = input('请输入语音时长')
                try:
                    t = int(t)
                except Exception:
                    print('输入错误!')
                    continue
                print('*开始录音*')
                if not os.path.exists('UserData/Cache'):
                    os.makedirs('UserData/Cache')
                filename = str(time.time()).split('.')[0] + '.wav'
                url = recordwav(t, os.path.join('UserData/Cache', filename))
                print('*结束录音*')
                fileName = url.split('/')[-1]
                try:
                    with open(url, 'rb') as f:
                        fileData = f.read()
                        # 进行b64编码
                        fileData = base64.urlsafe_b64encode(fileData).decode()
                        self.sendMessage(ClientAction.sendMsg, self.makeMsg(MessageType.mp3, fileData, filename=fileName))
                except Exception as err:
                    logging.error(err)
            elif op == '4':
                self.logout()

    def setCallback(self, callback):
        """用于UI界面的msg回调
        Args:
            callback: 回调函数
        """
        self.callback = callback

    def startRecving(self):
        def handleReceiveUI():
            while self.recving:
                if self.status == ClientStatus.online:
                    try:
                        # retMsg = client.recv(1024)
                        retMsg = recvWithCache(self.client, dict())[0]
                        retMsg = json.loads(retMsg)
                        if self.callback:
                            self.callback(retMsg)
                    except Exception:
                        pass
        self.recving = True
        wx.CallAfter(handleReceiveUI)

    def stopRecving(self):
        self.recving = False



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    client = Client()
    username = input('输入你的名称: ')
    client.initEnvironment('0.0.0.0', SOCKET_PORT, username)
    client.login()
    client.run()
