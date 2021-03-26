import socket
import json
import threading
import select
import copy
import logging
from './ChattingRoomModel' import *


def initEnvironment():
    """初始化环境变量
    """
    global client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect('0.0.0.0', 8000)

    username = input('输入你的名称')

    global status = ClientStatus.offline

def handleReceive():
    while True:
        if status == ClientStatus.offline:
            break
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
                    elif _action == ServerAction.onlineUsers.name:
                        logging.info('当前用户', _onlineUsers)
                    elif _action == ServerAction.newMessage.name:
                        loging.info('新信息', )

            else Exception err:
                logging.error(err)

