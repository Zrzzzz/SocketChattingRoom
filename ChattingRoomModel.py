from enum import Enum


# SOCKET端口号
SOCKET_PORT = 8000
# 信息类别，可以发送文本、文件和语音
MessageType = Enum('MessageType', ('text', 'file', 'mp3'))
# 客户端动作类别，用户可以登录、发送信息、退出
ClientAction = Enum('Action', ('login', 'logout', 'sendMsg', 'getOnline'))
# 服务端动作类别，返回在线用户、新信息等
ServerAction = Enum('ServerAction', ('loginSuccess', 'logoutSuccess',
'onlineUsers', 'newMessage', 'info'))
# 客户端状态
ClientStatus = Enum('ClientStatus', ('offline', 'online'))

"""服务器返回的信息格式
Args:
    status: int # 1 为 Ok 0 为 失败
    msg: str # 可以用来传输一些信息
    action: ServerAction
    data: json

json:
    msgs: [Message]
    onlineUsers: [str]
"""
retMessageModel = {
    'status': 0,
    'msg': '',
    'action': ServerAction.onlineUsers,
    'data': {
        'msgs': [],
        'onlineUsers': []
    }
}

"""用户发送的信息格式如下
Args:
    action: ClientAction
    user: str
    data: json

json:
    username: str
    time: Timestamp
    msg: data
"""
sendMessageModel = {
    'action': ClientAction.login,
    'user': '',
    'data': {
        'username': '',
        'time': 0,
        'msg': ''
    }
}

"""message格式为json
Args:
    from: str
    to: str
    time: Timestamp
    type: MessageType
    data: Bytes
"""
messageModel = {
    'from': '',
    'to': '',
    'time': '',
    'type': '',
    'data': '',
    # 如果是文件或者mp3
    'filename': ''
}


class ExitError(RuntimeError):
    def __init__(self, arg=''):
        self.args = arg


def recvWithCache(sock, cache):
    """带有缓存的接收数据

    Args:
        sock ( socket ): 维护客户端连接的套接字
        cache ( dict ): 缓存接收的数据
    Retruns:
        recvMsg ( str )
    """
    import re

    def decode(msg):
        matches = re.finditer(r"XISOSTART(\d{6})(\d{6})([\s\S]*?)(?=XI)|XISOSTART(\d{6})(\d{6})([\s\S]*)", msg, re.MULTILINE)
        for match in matches:
            g = match.groups()
            if g[0]:
                h, m, c = g[:3]
            else:
                h, m, c = g[3:]
            v = cache.get(h, [])
            if v:
                cache[h].append((m, c))
            else:
                cache[h] = [(m, c)]
    def flat(dic):
        ret = []
        for v in dic.values():
            print(len(v))
            s = sorted(v, key=lambda x: int(x[0]))
            t = ''
            for i in s:
                t += i[1]
            ret.append(t)
        return ret
    try:
        tmp = sock.recv(1024).decode()
        if len(tmp) == 0:
            raise SystemExit()
            return
        decode(tmp)
        while len(tmp) == 1024:
            tmp = sock.recv(1024).decode()
            if len(tmp) == 0:
                raise SystemExit()
                return
            decode(tmp)
        # 信息头部为XISOSTART和6位hash值与3位包序号组成
        return flat(cache)
    except Exception:
        raise Exception("CAN'T find start identifier!")


def sendWithCache(sock, msg):
    """自定义发送函数

    Args:
        sock ( socket ): 维护客户端连接的套接字
        msg ( str ): 需要发送的信息
    """
    import math
    length = 1024
    aLen = length - len('XISOSTART') - 12  # 减去首部长度
    msgArr = []
    if len(msg) > aLen:
        for i in range(math.ceil(len(msg) / aLen)):
            msgArr.append(msg[i * aLen: (i+1) * aLen])
    else:
        msgArr.append(msg)
    h = str(int(hash(msg) % 1E6))
    for i, m in enumerate(msgArr):
        sock.send('XISOSTART{0:0>6}{1:0>6}{2}'.format(h, i, m).encode())