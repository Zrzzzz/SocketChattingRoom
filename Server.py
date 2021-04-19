import socket
import json
import select
import copy
import logging
from ChattingRoomModel import *


class Server(object):
    def __init__(self):
        self.initEnvironment()

    def initEnvironment(self):
        """初始化环境变量
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', SOCKET_PORT))
        self.server.listen()

        # 创建一个epoll对象
        self.epoll = select.epoll()
        # 监听输入
        self.epoll.register(self.server.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLRDHUP | select.EPOLLERR)

        """
        维护一个用户列表
        Args:
            key: fd # socket.fileno()
            value: (socket, str) # the socket for username and username
        """
        self.userList = {}
        """
        message格式为json
        Args:
            from: str
            to: str
            time: Timestamp
            type: MessageType
            data: Bytes
        """
        self.messageList = []

    def createUser(self, sock, username=''):
        """用于处理用户登入

        Args:
            sock (socket): 维护连接的套接字
            username (str): 用户id
        """
        # 注册用户
        if self.userList.get(sock.fileno(), 0) == 0:
            self.epoll.register(sock.fileno(), select.EPOLLIN | select.EPOLLET | select.EPOLLRDHUP | select.EPOLLERR)
        self.userList[sock.fileno()] = (sock, username)
        
    def deleteUser(self, fd):
        """用于处理用户主动登出或者客户端离线

        Args:
            fd (socket.fileno()): 套接字的标识符
        """
        if fd in self.userList.keys():
            self.epoll.unregister(fd)
            self.userList[fd][0].close()
            logging.info('{} 已下线'.format(self.userList[fd][1]))
            del self.userList[fd]

    def handleRequest(self, sock):
        """用于处理客户端请求

        Args:
            sock (socket): 维护客户端连接的套接字
        """

        def sendMsgToSock(sock, status, msg, action, onlineUsers=[], msgs=[]):
            """对发送数据的封装

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
            # sock.send(json.dumps(retMsg).encode())
            sendWithCache(sock, json.dumps(retMsg))
            logging.info('发送回复, %s', msg)

        try:
            # 接收数据并解析
            recvMsg = recvWithCache(sock, dict())[0]
            recvMsg = json.loads(recvMsg)
            logging.info('接收到新信息')
            logging.info(recvMsg)
            _action = recvMsg['action']
            _user = recvMsg['user']
            _data = recvMsg['data']

            # 处理登入
            if _action == ClientAction.login.name:
                self.createUser(sock, _user)
                # 处理返回信息
                users = list(filter(lambda x: x != '', map(lambda x: x[1], self.userList.values())))
                sendMsgToSock(sock, True, '登入成功', ServerAction.loginSuccess, onlineUsers=users)
                # 给其他人发送已登入
                for user in self.userList.values():
                    if user[1] != _user:
                        msg = '%s加入了聊天室' % _user
                        sendMsgToSock(user[0], True, msg, ServerAction.info)
            # 处理登出
            elif _action == ClientAction.logout.name:
                # 处理返回信息
                sendMsgToSock(sock, True, '登出成功', ServerAction.logoutSuccess)
                # 只要做离线处理即可
                self.deleteUser(sock.fileno())
            # 处理发送数据
            elif _action == ClientAction.sendMsg.name:
                _message = _data['msg']
                self.messageList.append(_message)
                # 发送信息
                for user in self.userList.values():
                    if user[1] != _user:
                        sendMsgToSock(user[0], True, '新信息', ServerAction.newMessage, msgs=[_message])

            # 处理获取在线用户
            elif _action == ClientAction.getOnline.name:
                users = list(filter(lambda x: x != '', map(lambda x: x[1], self.userList.values())))
                sendMsgToSock(sock, True, '获取在线用户成功', ServerAction.info, onlineUsers=users)
        except SystemExit:
            # 可能直接退出客户端或者停止进程
            self.deleteUser(sock.fileno())
        except Exception as err:
            logging.error('信息处理失败 %s', err)

    def run(self):
        """轮询事件
        """
        while True:
            logging.info('开始轮询')
            events = self.epoll.poll(10)
            if not events:
                logging.info('本次未接收到事件')
                continue
            else:
                logging.info('接收到事件')
                for fd, event in events:
                    # 对服务端的连接
                    if fd == self.server.fileno():
                        sock, addr = self.server.accept()
                        logging.info('建立连接, addr: {}'.format(addr))
                        # 建立用户
                        self.createUser(sock)

                    # 客户端输入
                    elif event & select.EPOLLIN:
                        sock = self.userList.get(fd, (0,0))[0]
                        if sock == 0:
                            logging.error('用户查询失败')
                        else:
                            self.handleRequest(sock)
                        # 客户端挂起
                    elif event & select.EPOLLHUP:
                        # TODO: 处理用户挂起
                        logging.info('挂起')
                    else:
                        print('event: ', event)
                        self.deleteUser(fd)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server = Server()
    server.run()
