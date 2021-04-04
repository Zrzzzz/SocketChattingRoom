import wx


class ClientMainView(wx.Frame):
    def __init__(self, parent, id, updater):
        super().__init__(parent=parent, id=id, title="XI Client", size=(400, 400))
        self.updater = updater
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
