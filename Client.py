import socket
import json
import threading
import select
import copy
import logging
import time
from ChattingRoomModel import *


def timestampToString(timestamp):
    t = time.localtime(timestamp)
    w = time.strftime("%Y-%m-%d %H:%M:%S", t)
    return w


def printMessage(msgs):
    for msg in msgs:
        if msg['type'] == MessageType.text.name:
            print("{} {}:\n{}".format(msg['from'], timestampToString(
                msg['time']), msg['data']))


def sendMessage(action, msg=None):
    global client
    sendMsg = copy.deepcopy(sendMessageModel)
    sendMsg['action'] = action.name
    sendMsg['user'] = user
    if msg:
        sendMsg['data'] = {
            'username': user,
            'time': time.time(),
            'msg': msg
        }
    client.send(json.dumps(sendMsg).encode())


def login():
    global status
    sendMessage(ClientAction.login)
    status = ClientStatus.online


def logout():
    global status
    sendMessage(ClientAction.logout)
    status = ClientStatus.offline


def initEnvironment():
    """初始化环境变量
    """
    global client, user, status
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('0.0.0.0', 8001))

    user = input('输入你的名称: ')

    status = ClientStatus.offline
    login()


def handleReceive():
    global status
    while True:
        if status == ClientStatus.offline:
            continue
        else:
            try:
                retMsg = client.recv(1024)
                retMsg = json.loads(retMsg.decode())
                # 对消息状态进行判断
                if retMsg['status'] == 0:
                    logging.info('请求失败', retMsg['msg'])
                else:
                    logging.info('请求成功')
                    _action = retMsg['action']
                    _msgs = retMsg['data']['msgs']
                    _onlineUsers = retMsg['data']['onlineUsers']

                    if _action == ServerAction.info.name:
                        logging.info(retMsg['msg'])
                    elif _action == ServerAction.loginSuccess.name:
                        logging.info('欢迎您 {}\n当前在线用户: {}'.format(user, _onlineUsers))
                    elif _action == ServerAction.logoutSuccess.name:
                        logging.info('已登出')
                        status = ClientStatus.offline
                        break
                    elif _action == ServerAction.newMessage.name:
                        logging.info('新信息')
                        printMessage(_msgs)
                        print('end')

            except Exception as err:
                logging.error(err)


def makeMsg(type, dataStr, to=''):
    msg = copy.deepcopy(messageModel)
    msg['from'] = user
    msg['to'] = to
    msg['time'] = time.time()
    msg['type'] = type.name
    msg['data'] = dataStr
    return msg


def handleRequest():
    while True:
        op = input(
            '请输入要进行的操作: \n1: send text\n2: send file\n3: send voice\n4: exit\n')
        if op not in list(map(str, [1, 2, 3, 4])):
            print('无效操作')
            continue
        if op == '4':
            logout()
        if op == '1':
            text = input('发一句友善的话: ')
            sendMessage(ClientAction.sendMsg, makeMsg(MessageType.text, text))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    initEnvironment()
    sendThread, recvThread = threading.Thread(target=handleRequest), threading.Thread(target=handleReceive)
    sendThread.start()
    recvThread.start()
