import wx
import socket
import json
import threading
import _thread as thread
import copy
import logging
import time
import base64
from ChattingRoomModel import *
from AudioHelper import recordwav, playwav
from wx.lib.newevent import NewEvent

class ClientMainView(wx.Frame):
    def __init__(self, parent, id, updater, client, user):
        super().__init__(parent=parent, id=id, title="XI Client", size=(400, 400))
        self.updater = updater
        self.client = client
        self.user = user

        self.status = ClientStatus.online
        self.recving = False
        self.onlineUsers = []
        self.InitUI()
        self.startRecving()
        self.sendMessage(ClientAction.getOnline)

    def InitUI(self):
        self.Center()
        panel = wx.Panel(parent=self)
        contentView = wx.BoxSizer(wx.HORIZONTAL)
        # 对话框、工具栏、发送框
        interactView = wx.BoxSizer(wx.VERTICAL)
       
        # 添加相关组件
        self.dialogView = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        utilView = wx.BoxSizer(wx.HORIZONTAL)
        self.inputView = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER | wx.TE_MULTILINE)
        self.inputView.Bind(wx.EVT_TEXT_ENTER, self.inputViewOnEnter)
        
        interactView.Add(self.dialogView, 4, wx.EXPAND)
        interactView.Add(utilView, 1, wx.EXPAND)
        interactView.Add(self.inputView, 2, wx.EXPAND)

        # 工具栏
        filebm = wx.Bitmap("assets/file.png", wx.BITMAP_TYPE_PNG)
        filebm = wx.ImageFromBitmap(filebm).Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        filebm = wx.BitmapFromImage(filebm)
        self.fileBtn = wx.BitmapButton(panel, bitmap=filebm, size=(40, 40))
        self.fileBtn.Bind(wx.EVT_BUTTON, self.sendFile)
        voicebm = wx.Bitmap("assets/voice.png", wx.BITMAP_TYPE_PNG)
        voicebm = wx.ImageFromBitmap(voicebm).Scale(20, 20, wx.IMAGE_QUALITY_HIGH)
        voicebm = wx.BitmapFromImage(voicebm)
        self.voiceBtn = wx.BitmapButton(panel, bitmap=voicebm, size=(40, 40))
        self.voiceBtn.Bind(wx.EVT_LEFT_DOWN, self.sendVoiceStart)
        self.voiceBtn.Bind(wx.EVT_LEFT_UP, self.sendVoiceEnd)
        utilView.Add(self.fileBtn)
        utilView.Add(self.voiceBtn)        

        # 用户列表
        userView = wx.BoxSizer(wx.VERTICAL)
        self.userLabel = wx.StaticText(panel, -1, "在线用户: %s" % len(self.onlineUsers))
        userView.Add(self.userLabel)
        self.userListView = wx.ListBox(panel, choices=self.onlineUsers, style=wx.LB_SINGLE)
        userView.Add(self.userListView, 1, wx.EXPAND)

        contentView.Add(interactView, 2, wx.EXPAND)
        contentView.Add((10, 0))
        contentView.Add(userView, 1, wx.EXPAND)

        panel.SetSizerAndFit(contentView)
        self.Center()

    def inputViewOnEnter(self, evt):
        s = self.inputView.GetValue()
        self.inputView.SetValue('')
        self.sendMessage(ClientAction.sendMsg, self.makeMsg(MessageType.text, s))
        self.dialogView.AppendText("{} {}:\n{}\n\n".format('你', self.__timestampToString(
                    time.time()), s))

    def sendFile(self, evt):
        import os
        wildcard = 'All files(*.*)|*.*'
        with wx.FileDialog(self,
                           '选取文件',
                           os.getcwd(),
                           '',
                           wildcard,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            fileUrl = ''
            fileData = None
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            fileUrl = dialog.GetPath()
            print(fileUrl)
            fileName = fileUrl.split('/')[-1]
            with open(fileUrl, 'rb') as f:
                fileData = f.read()
                fileData = base64.urlsafe_b64encode(fileData).decode()
                self.sendMessage(ClientAction.sendMsg, self.makeMsg(MessageType.file, fileData, filename=fileName))

    def saveFile(self, fileData, filename):
        import os
        with wx.FileDialog(self, '保存文件至', os.getcwd(), 
                           filename, 'All files (*.*)|*.*', wx.FD_SAVE) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.file_name = dialog.GetFilename()
                self.dir_name = dialog.GetDirectory()
                url = os.path.join(self.dir_name, self.file_name)
                try:
                    with open(url, 'wb') as f:
                        _data = fileData
                        _data += '=' * (-len(_data) % 4)
                        _data = base64.urlsafe_b64decode(_data.encode())
                        f.write(_data)
                        wx.MessageDialog(self, '文件已保存', '提示')
                except FileNotFoundError:
                    wx.MessageDialog(self, '保存失败,无效的保存路径', '提示')   

    def sendVoiceStart(self, evt):
        self.isrecoding = True
        if not os.path.exists('UserData/Cache'):
                    os.makedirs('UserData/Cache')
        filename = str(time.time()).split('.')[0] + '.wav'
        url = recordwav(0, os.path.join('UserData/Cache', filename), self.isrecoding)
        fileName = url.split('/')[-1]
        try:
            with open(url, 'rb') as f:
                fileData = f.read()
                # 进行b64编码
                fileData = base64.urlsafe_b64encode(fileData).decode()
                self.sendMessage(ClientAction.sendMsg, self.makeMsg(MessageType.mp3, fileData, filename=fileName))
        except Exception as err:
            logging.error(err)
    def sendVoiceEnd(self, evt):
        self.isrecoding = False

    def startRecving(self):
        self.recving = True
        thread.start_new_thread(self.handleReceive, ())

    def stopRecving(self):
        self.recving = False

    def handleReceive(self):
        while self.recving:
            time.sleep(0.5)
            if self.status == ClientStatus.offline:
                continue
            else:
                try:
                    retMsg = recvWithCache(self.client.client, dict())[0]
                    retMsg = json.loads(retMsg)
                    wx.CallAfter(self.handleData, retMsg)
                except Exception as err:
                    logging.error(err)

    def handleData(self, retMsg):
        """在主线程中调用，与cli上有区别"""
        # 对消息状态进行判断
        if retMsg['status'] == 0:
            logging.info('请求失败', retMsg['msg'])
        else:
            logging.info('请求成功')
            _action = retMsg['action']
            _msgs = retMsg['data']['msgs']
            _onlineUsers = retMsg['data']['onlineUsers']

            if _action == ServerAction.info.name:
                if _onlineUsers:
                    self.onlineUsers = _onlineUsers
                    """更新数据"""
                    self.userLabel.SetLabel("在线用户: %s" % len(self.onlineUsers))
                    self.userListView.Clear()
                    for i in self.onlineUsers:
                        self.userListView.Append(i)
                self.dialogView.AppendText("Notice:\n{}\n\n".format(retMsg['msg']))
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

    def handleMessage(self, msgs):
        import base64
        for msg in msgs:
            _type = msg['type']
            if _type == MessageType.text.name:
                self.dialogView.AppendText("{} {}:\n{}\n\n".format(msg['from'], self.__timestampToString(
                    msg['time']), msg['data']))
            elif _type == MessageType.file.name:
                with wx.MessageDialog(None, 
                                       "接收到来自{}的文件{}\n是否接受".format(msg['from'], msg['filename']), 
                                       "新文件", wx.YES_NO | wx.ICON_QUESTION) as dlg:
                    if dlg.ShowModal() == wx.ID_YES:
                        self.saveFile(msg['data'], msg['filename'])
                # import os
                # filePath = 'UserData/Download'
                # if not os.path.exists(filePath):
                #     os.makedirs(filePath)
                # url = os.path.join(filePath, msg['filename'])
                # with open(url, 'wb') as f:
                #     _data = msg['data']
                #     _data += '=' * (-len(_data) % 4)
                #     _data = base64.urlsafe_b64decode(_data.encode())
                #     f.write(_data)
                #     print("{} {}:\n发送了文件:{}, 存放至{}".format(msg['from'], self.__timestampToString(msg['time']), msg['filename'], url))
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

    def __timestampToString(self, timestamp):
        t = time.localtime(timestamp)
        w = time.strftime("%Y-%m-%d %H:%M:%S", t)
        return w

    def makeMsg(self, type, dataStr, to='', filename=''):
        msg = copy.deepcopy(messageModel)
        msg['from'] = self.user
        msg['to'] = to
        msg['time'] = time.time()
        msg['type'] = type.name
        msg['data'] = dataStr
        msg['filename'] = filename
        return msg

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
        sendWithCache(self.client.client, json.dumps(sendMsg))
