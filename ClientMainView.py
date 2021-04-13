import wx


class ClientMainView(wx.Frame):
    def __init__(self, parent, id, updater, client):
        super().__init__(parent=parent, id=id, title="XI Client", size=(400, 400))
        self.updater = updater
        self.client = client
        self.InitUI()

    def InitUI(self):
        self.Center()
        panel = wx.Panel(parent=self)
        contentView = wx.BoxSizer(wx.HORIZONTAL)
        # 对话框、工具栏、发送框
        interactView = wx.BoxSizer(wx.VERTICAL)
       
        # 添加相关组件
        self.dialogView = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        utilView = wx.BoxSizer(wx.HORIZONTAL)
        self.inputView = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.inputView.Bind(wx.EVT_TEXT_ENTER, self.sendMessage)
        
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
        self.onlineUsers = ['zzx', 'zzzxz', 'adwda']
        userView = wx.BoxSizer(wx.VERTICAL)
        userLabel = wx.StaticText(panel, -1, "在线用户: %s" % len(self.onlineUsers))
        userView.Add(userLabel)
        userListView = wx.ListBox(panel, choices=self.onlineUsers, style=wx.LB_SINGLE)
        userView.Add(userListView, 1, wx.EXPAND)

        contentView.Add(interactView, 2, wx.EXPAND)
        contentView.Add((10, 0))
        contentView.Add(userView, 1, wx.EXPAND)

        panel.SetSizerAndFit(contentView)
        self.Center()

    def sendMessage(self, evt):
        s = self.inputView.GetValue()
        self.inputView.SetValue('')
        self.dialogView.AppendText(s + '\n')

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
            with open(fileUrl, 'rb') as f:
                fileData = f.read()
            print(fileData.decode())

    def sendVoiceStart(self, evt):
        print("开始录音")

    def sendVoiceEnd(self, evt):
        print("结束录音")