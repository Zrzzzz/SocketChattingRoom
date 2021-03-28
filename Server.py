import socket
import json
import select
import copy
import logging
import demjson
from ChattingRoomModel import *


def initEnvironment():
    """初始化环境变量
    """
    global server, epoll, userList, messageList
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 8001))
    server.listen()

    # 创建一个epoll对象
    epoll = select.epoll()
    # 监听输入
    epoll.register(server.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLRDHUP | select.EPOLLERR)

    """
    维护一个用户列表
    Args:
        key: fd # socket.fileno()
        value: (socket, str) # the socket for username and username
    """
    userList = {}
    """
    message格式为json
    Args:
        from: str
        to: str
        time: Timestamp
        type: MessageType
        data: Bytes
    """
    messageList = []


def createUser(sock, username=''):
    """用于处理用户登入

    Args:
        sock (socket): 维护连接的套接字
        username (str): 用户id
    """
    # 注册用户
    if userList.get(sock.fileno(), 0) == 0:
        epoll.register(sock.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLRDHUP | select.EPOLLERR)
    userList[sock.fileno()] = (sock, username)
    

def deleteUser(fd):
    """用于处理用户主动登出或者客户端离线

    Args:
        fd (socket.fileno()): 套接字的标识符
    """
    if sock.fileno() in userList.keys():
        epoll.unregister(sock.fileno())
        userList[sock.fileno()][0].close()
        logging.info('{} 已下线'.format(userList[sock.fileno()][1]))
        del userList[sock.fileno()]


def handleRequest(sock):
    """用于处理客户端请求

    Args:
        sock (socket): 维护客户端连接的套接字
    """
    # 接收数据并解析
    recvMsg = sock.recv(1024)
    retMsg = copy.deepcopy(retMessageModel)

    def sendMsgToSock(sock, status, msg, action, onlineUsers=[], msgs=[]):
        """对发送数据的封装

        TODO: 增加包头
        Args:
            sock (socket): 维护客户端连接的套接字
            status (int): 是否成功
            msg (str): 信息
            action (ServerAction): 服务端行为
            onlineUsers (list)
            msgs (list)
        """
        retMsg = {
            'status': status,
            'msg': msg,
            'action': action.name,
            'data': {
                'msgs': msgs,
                'onlineUsers': onlineUsers
            }
        }
        sock.send(json.dumps(retMsg).encode())
        logging.info('发送回复, %s', msg)

    try:
        recvMsg = json.loads(recvMsg.decode())
        logging.info('接收到新信息')
        _action = recvMsg['action']
        _user = recvMsg['user']
        _data = recvMsg['data']

        # 处理登入
        if _action == ClientAction.login.name:
            createUser(sock, _user)
            # 处理返回信息
            sendMsgToSock(sock, True, '登入成功', ServerAction.loginSuccess, onlineUsers=list(map(lambda x: x[1], userList.values())))
        # 处理登出
        elif _action == ClientAction.logout.name:
            # 只要做离线处理即可
            deleteUser(sock.fileno())
            # 处理返回信息
            sendMsgToSock(sock, True, '登出成功', ServerAction.logoutSuccess)
        # 处理发送数据
        elif _action == ClientAction.sendMsg.name:
            _message = _data['msg']
            messageList.append(_message)
            # 发送信息
            for user in userList.values():
                sendMsgToSock(user[0], True, '新信息', ServerAction.newMessage, msgs=[_message])

        # 处理获取在线用户
        elif _action == ClientAction.getOnline.name:
            # TODO: 获取在线用户
            pass
    except Exception as err:
        logging.error('信息处理失败 %s', err)


def main():
    """轮询事件
    """
    while True:
        logging.info('开始轮询')
        events = epoll.poll(10)
        if not events:
            logging.info('本次未接收到事件')
            continue
        else:
            logging.info('接收到事件')
            for fd, event in events:
                # 对服务端的连接
                if fd == server.fileno():
                    sock, addr = server.accept()
                    logging.info('建立连接, addr: {}'.format(addr))
                    # 建立用户
                    createUser(sock)

                # 客户端输入
                elif event & select.EPOLLIN:
                    sock = userList.get(fd, (0,0))[0]
                    if sock == 0:
                        logging.error('用户查询失败')
                    else:
                        handleRequest(sock)
                    # 客户端挂起
                elif event & select.EPOLLHUP:
                    # TODO: 处理用户挂起
                    pass
                    # 结束客户端连接
                else:
                    deleteUser(fd)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    initEnvironment()
    main()
