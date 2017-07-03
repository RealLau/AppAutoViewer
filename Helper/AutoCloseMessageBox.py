import wx

class MessageDialog(wx.Dialog):
    def __init__(self, message, title):
        wx.Dialog.__init__(self, None, -1, title,size=(300, 120))
        self.CenterOnScreen(wx.BOTH)
        text = wx.StaticText(self, -1, message)
        ok = wx.Button(self, wx.ID_OK, "确认已经加载完成，我要马上结束")
        ok.SetDefault()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(text, 1, wx.ALIGN_CENTER|wx.TOP, 10)
        vbox.Add(ok, 1, wx.ALIGN_CENTER|wx.BOTTOM, 10)
        self.SetSizer(vbox)
