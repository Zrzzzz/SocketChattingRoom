import wx
from ClientMainView import ClientMainView
from ClientLoginView import ClientLoginView


class GuiManager():
    def __init__(self, UpdateUI):
        self.UpdateUI = UpdateUI
        self.frameDict = {}  # 用来装载已经创建的Frame对象
 
    def GetFrame(self, type):
        frame = self.frameDict.get(type)
 
        if frame is None:
            frame = self.CreateFrame(type)
            self.frameDict[type] = frame
 
        return frame
 
    def CreateFrame(self, type):
        if type == 0:
            return ClientLoginView(parent=None, id=type, updater=self.UpdateUI)
        elif type == 1:
            return ClientMainView(parent=None, id=type, updater=self.UpdateUI)