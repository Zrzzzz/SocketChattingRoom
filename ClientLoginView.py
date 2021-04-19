import wx


class ClientLoginView(wx.Frame):
    def __init__(self, parent, id, updater, client):
        super(ClientLoginView, self).__init__(parent, id=id, title="登录", style=wx.DEFAULT_FRAME_STYLE^wx.MAXIMIZE_BOX, size=(400,150))

        self.updater = updater
        self.client = client
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        contentView = wx.BoxSizer(wx.VERTICAL)

        # 连接服务器的参数
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        l1 = wx.StaticText(panel, -1, "服务器地址")
        self.serverTF = wx.TextCtrl(panel)
        l2 = wx.StaticText(panel, -1, "端口")
        self.portTF = wx.TextCtrl(panel)
        # 添加小视图到hbox里
        hbox1.Add(l1, 2, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)
        hbox1.Add(self.serverTF, 1, wx.ALIGN_LEFT, 0)
        hbox1.AddSpacer(5)
        hbox1.Add(l2, 1, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)
        hbox1.Add(self.portTF, 1, wx.ALIGN_LEFT, 0)
        # 添加hbox到主视图中
        contentView.Add(hbox1, 1, wx.LEFT | wx.RIGHT, 10)
        contentView.AddSpacer(10)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        l3 = wx.StaticText(panel, -1, "用户名")
        self.userTF = wx.TextCtrl(panel)
        hbox2.Add(l3, 2, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)
        hbox2.Add(self.userTF, 1, wx.ALIGN_LEFT, 0)

        contentView.Add(hbox2, 1, wx.LEFT | wx.RIGHT, 10)
        contentView.AddSpacer(20)

        self.btn = wx.Button(panel, -1, "登录")
        contentView.Add(self.btn, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM, 0)
        self.btn.Bind(wx.EVT_BUTTON, self.login)

        panel.SetSizerAndFit(contentView)
        panel.Fit()
        self.Center()

    def login(self, evt):
        # serverAddr = self.serverTF.GetValue()
        # port = self.portTF.GetValue()
        # username = self.userTF.GetValue()

        # self.client.initEnvironment(serverAddr, int(port), username)
        self.client.initEnvironment('0.0.0.0', 8000, 'zzx')

        def messageCallback(msg):
            if msg['status'] == 1:
                # 停止接收，不然线程循环导致了UI无法更新
                self.client.stopRecving()
                # self.updater(1, username)
                self.updater(1, 'zzx')
            else:
                wx.MessageBox("登录失败", "错误", wx.OK | wx.ICON_INFORMATION)
        self.client.setCallback(messageCallback)
        self.client.login()
        self.client.startRecving()
