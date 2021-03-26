from enum import Enum

# 信息类别，可以发送文本、文件和语音
MessageType = Enum('MessageType', ('text', 'file', 'mp3'))
# 客户端动作类别，用户可以登录、发送信息、退出
ClientAction = Enum('Action', ('login', 'logout', 'sendMsg', 'getOnline'))
# 服务端动作类别，返回在线用户、新信息等
ServerAction = Enum('ServerAction', ('onlineUsers', 'newMessage', 'info'))
# 客户端状态
ClientStatus = Enum('ClientStatus', ('offline', 'online'))

"""
用户发送的信息格式如下
Args:
    action: ClientAction
    user: str
    data: json

json:
    username: str
    time: Timestamp
    type: MessageType
    msg: data

服务器返回的信息格式
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
    'action': ServerAction.onlineUser
    'data': {
        'msgs': [],
        'onlineUsers': []
    }
}

sendMessageModel = {
    'action': Action.login,
    'user': '',
    'data': {
        'username': '',
        'time': 0,
        'msgType': MessageType.text,
        'msg': ''
    }
}

if __name__ == '__main__':
    print(Action.login)
