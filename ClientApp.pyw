import wx
from ClientMainView import ClientMainView
from ClientLoginView import ClientLoginView
import UIManager
import Client as ClientManager


class ClientApp(wx.App):
    def OnInit(self):
        self.manager = UIManager.GuiManager(self.updateUI)
        self.client = ClientManager.Client()
        self.frame = self.manager.GetFrame(0, self.client)
        self.frame.Show()
        return True

    def OnExit(self):
        print('exit')
        return 0

    def updateUI(self, order):
        self.frame.Show(False)
        self.frame = self.manager.GetFrame(order, self.client)
        self.frame.Show()


if __name__ == '__main__':
    app = ClientApp()
    app.MainLoop()