import wx
import os
import wx.lib.scrolledpanel as scrolled
from wx.lib.pubsub import pub
from threading import Thread
import subprocess
from Helper.xmlTree import XMLTree
from Helper.AutoCloseMessageBox import MessageDialog
import wx.grid as GD
from collections import OrderedDict
from wx.lib.intctrl import IntCtrl as IntC
from PIL import Image

recordStatus = None
recordTimeDelay = None
nodeDetailData = None
treeDic = None
isDoingRecording = False

class getNewScreenShotAndDomFileThread(Thread):
    def __init__(self):
        #线程实例化时立即启动
        Thread.__init__(self)
        self.start()
    def checkDevice(self, out):
        s = out.replace("List of devices attached", "").replace("\t", "").replace("\r", "").replace("\n", "").replace("device", "")
        if s=="" or "." in s:
            return False
        else:
            return True
        
    def run(self):
        try:
            os.remove(os.path.join(os.getcwd(),"Hierarchy","window_dump.xml"))
        except:
            pass
        #获取设备连接信息，页面截图，以及布局文件
        wx.CallAfter(pub.sendMessage,"update", msg = u"获取设备信息中……")
        #获取设备局信息
        p =  subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(p.communicate(timeout=10))
        out = p.communicate(timeout=10)[0].decode()
        deviceStatus = self.checkDevice(out)
        msg = None
        if deviceStatus:
            msg = "获取设备信息成功"
            wx.CallAfter(pub.sendMessage,"update", msg = msg)
            #获取页面截图文件
            wx.CallAfter(pub.sendMessage,"update", msg = u"获取页面截图中……")
            print(msg)
            print("获取页面截图中……")
            p =  subprocess.Popen("adb shell /system/bin/screencap -p /sdcard/screenshot.png", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate(timeout=10)
            outPut = (out[0].decode()+out[1].decode()).replace("\r","").replace("\n","")
            if "error" in outPut:
                msg = "获取页面截图失败: "+outPut
                wx.CallAfter(pub.sendMessage,"update", msg = msg)
                print(msg)
                return
            else:
                msg = "获取页面截图成功"
                wx.CallAfter(pub.sendMessage,"update", msg = msg)
                print(msg)
                #上传截图文件至PC：当前目录的screenShot下
                wx.CallAfter(pub.sendMessage,"update", msg = "上传页面截图至PC……")
                cDir = os.getcwd()
                screenShotPath = os.path.join(cDir,"screenShot","screenshot.png")
                p =  subprocess.Popen("adb pull /sdcard/screenshot.png %s" % screenShotPath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate(timeout=10)
                outPut = (out[0].decode()+out[1].decode()).replace("\r","").replace("\n","")
                if "error" in outPut:
                    msg = "上传页面截图至PC失败: "+outPut
                    print(msg)
                    return 
                else:
                    msg = "上传页面截图至PC成功"
                    print(msg)
                    wx.CallAfter(pub.sendMessage,"update", msg = msg)
                    wx.CallAfter(pub.sendMessage,"update", msg = screenShotPath)
                    #获取页面布局文件adb shell uiautomator dump /mnt/sdcard/window_dump.xml  获得手机当前界面的UI信息，生成window_dump.xml
                    msg = "获取页面布局文件中……"
                    print(msg)
                    wx.CallAfter(pub.sendMessage,"update", msg = msg)
                    p =  subprocess.Popen("adb shell uiautomator dump /sdcard/window_dump.xml", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = p.communicate(timeout=20)
                    outPut = (out[0].decode()+out[1].decode()).replace("\r","").replace("\n","")
                    if "error" in outPut or "ERROR" in outPut:
                        msg = "获取页面布局文件失败: "+outPut+"动态页面不支持获取（建议：暂停播放后重试）"
                        print(msg)
                        wx.CallAfter(pub.sendMessage,"update", msg = msg)
                    else:
                        msg = "获取页面布局文件成功"
                        print(msg)
                        wx.CallAfter(pub.sendMessage,"update", msg = msg)
                        #上传页面布局文件至PC：当前目录的Hierarchy下
                        print("上传页面截图至PC……")
                        wx.CallAfter(pub.sendMessage,"update", msg = "上传页面截图至PC……")
                        xmlHierarchyPath = os.path.join(cDir,"Hierarchy","window_dump.xml")
                        p =  subprocess.Popen("adb pull /sdcard/window_dump.xml %s" % xmlHierarchyPath, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out = p.communicate(timeout=20)
                        outPut = (out[0].decode()+out[1].decode()).replace("\r","").replace("\n","")
                        if "error" in outPut:
                            msg = "上传页面布局文件至PC失败: "+outPut
                            print(msg)
                            wx.CallAfter(pub.sendMessage,"update", msg = msg)
                            return 
                        else:
                            msg = "上传页面布局文件至PC成功"
                            wx.CallAfter(pub.sendMessage,"update", msg = msg)
                            wx.CallAfter(pub.sendMessage,"update", msg = xmlHierarchyPath)
                            wx.CallAfter(pub.sendMessage,"updateTree")
                            print(msg)
                            wx.CallAfter(pub.sendMessage, "updateNodeDetail")
        else:
            msg = "获取设备信息失败: 请确认安卓设备与PC连接良好后重试"  
            wx.CallAfter(pub.sendMessage,"update", msg = msg)
            print(msg)
            return

########################################################################
class LeftPanel(scrolled.ScrolledPanel):
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        self.notUseDetaul = None
        wx.Panel.__init__(self, parent=parent, size = (500,800))
        B = wx.StaticBox(self, -1)
        BSizer = wx.StaticBoxSizer(B, wx.VERTICAL)
        self.imagesDir = os.path.join(".", "images")
        self.screenShotDir = os.path.join(".", "screenShot")
        self.defaultScreenShotImage = wx.Image(os.path.join(self.imagesDir, "default.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.screenShot = wx.StaticBitmap(self,-1, self.defaultScreenShotImage)
        self.screenShot.Bind(wx.EVT_LEFT_DOWN, self.DrawOrReloadAll)
        self.statusBar = wx.StaticText(self, -1, "")
        BSizer.Add(self.statusBar)
        BSizer.Add(self.screenShot,5,wx.EXPAND, 5)
        self.SetSizer(BSizer)
        pub.subscribe(self.updateStatus, "update")
        pub.subscribe(self.DrawFromSelectedNode, "DrawFromSelectedNode")
        pub.subscribe(self.DoSwipeOrInput, "DoSwipeOrInput")
        self.hasDrew = False
        
    def DrawFromSelectedNode(self, msg):
        t = msg.replace("][", ",").replace("[", "").replace("]", "").split(",")
        osx = int(t[0])
        osy = int(t[1])
        oex = int(t[2])
        oey = int(t[3])
        i = wx.Bitmap(os.path.join(self.screenShotDir, "screenshot.png"))
        dc = wx.MemoryDC(i)
        dc.SetPen(wx.Pen(wx.RED, 1))
        #画矩形(wxpython里需要用drawline或drawlines, 因为drawrect是画实心矩形)
        dc.DrawLine(osx, osy, osx, oey)
        dc.DrawLine(osx, osy, oex, osy)
        dc.DrawLine(oex, osy, oex, oey)
        dc.DrawLine(osx, oey, oex, oey)
        dc.SelectObject(wx.NullBitmap)
        self.screenShot.SetBitmap(i) 
        self.Refresh(eraseBackground=True, rect=None)
        
    def clearScreenShot(self, bmp):
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetBackground(wx.Brush("white"))
        dc.Clear()
        
    def updateStatus(self, msg):
#         siz = self.GetSize()
        if os.path.isfile(msg):
            if ".png" in msg:
                self.clearScreenShot(self.defaultScreenShotImage)
                newScreenShotPath = os.path.join(self.screenShotDir, "screenshot.png")
                self.newScreenShot = wx.Bitmap(newScreenShotPath)
                print("获取的截屏大小：",self.newScreenShot.GetSize())
                self.screenShot.SetBitmap(self.newScreenShot)
                self.Refresh(eraseBackground=True, rect=None)
                self.notUseDetaul = 1
            else:
                pass
        else:
            if msg == "上传页面布局文件至PC成功":
                self.statusBar.ForegroundColour = "red"
                self.statusBar.SetLabel(msg)
            else:
                self.statusBar.ForegroundColour = "blue"
                if "ERROR: could not get idle state." in msg:
                    self.statusBar.SetLabel(msg)
                self.statusBar.SetLabel(msg)
    
    def DoSwipeOrInput(self, msg):
        global recordStatus
        global treeDic
        global recordTimeDelay
        if treeDic!=None:
            if recordStatus=="开":
                if "滑动" in msg:
                    d = msg.replace("滑动\n", "").split("\n")
                    print("命令：滑动,", "移动点: ",d)
                    os.system("adb shell input swipe %d %d %d %d" % (int(d[0]), int(d[1]),int(d[2]),int(d[3])))

                    dlg = MessageDialog('等待新的页面加载完成(已设置延时%d秒)' % recordTimeDelay, '提示')        
                    wx.CallLater(recordTimeDelay*1000, dlg.Destroy)
                    dlg.ShowModal()
                    getNewScreenShotAndDomFileThread()  
                else:
                    c = msg.split("\n")[0]
                    kT = msg.split("\n")[1]
                    print("命令：输入,", "内容：",c)
                    if c!='':
                        if kT == "ADB":
                            os.system("adb shell am broadcast -a ADB_INPUT_TEXT --es msg '%s'" %c)
                        else:
                            os.system("adb shell input text '%s'" %c)
                        
                        dlg = MessageDialog('等待新的页面加载完成(已设置延时%d秒)' % recordTimeDelay, '提示')        
                        wx.CallLater(recordTimeDelay*1000, dlg.Destroy)
                        dlg.ShowModal()
                        getNewScreenShotAndDomFileThread()
                    else:
                        dlg = wx.MessageDialog(self, u"请检查输入内容", u"输入内容不能为空", wx.OK | wx.ICON_ERROR)
                        if dlg.ShowModal() == wx.ID_OK:
                            dlg.Destroy()
            else:
                msg = "要执行所选操作，请先打开同步模式"
                print(msg)
                wx.CallAfter(pub.sendMessage, "update", msg=msg)
        else:
            msg = "请先获取页面截图和布局文件"
            print(msg)
            wx.CallAfter(pub.sendMessage, "update", msg=msg)
           
    def DrawOrReloadAll(self, e):
        pos = e.GetPosition()
        print("detected click point:")
        print(pos)
        x = pos[0]
        y = pos[1]
        global treeDic
        if treeDic!=None:
            global recordStatus
            if recordStatus=="开":
                print("命令：点击", (x,y))
                os.system("adb shell input tap %d %d" % (x, y))
                global recordTimeDelay
                dlg = MessageDialog('等待新的页面加载完成(已设置延时%d秒)' % recordTimeDelay, '提示')        
                wx.CallLater(recordTimeDelay*1000, dlg.Destroy)
                dlg.ShowModal()
                getNewScreenShotAndDomFileThread()
            else:
                
                ind = 0
                d = OrderedDict()
                poin = []
                #找出被点击的点所在的最小矩形(该矩形对应节点的bounds属性)
                for v in treeDic.values():
                    #根节点：{'rotation':1}不管
                    if ind ==0:
                        pass
                    else:
                        b = v["bounds"]
                        t = b.replace("][", ",").replace("[", "").replace("]", "").split(",")
                        osx = int(t[0])
                        osy = int(t[1])
                        oex = int(t[2])
                        oey = int(t[3])
                        if x>osx and y>osy and x<oex and y<oey:
                            poin.append((osx, osy, oex, oey))
                            d[b] = (osx, osy, oex, oey)
                    ind += 1
                m = 0
                ind = 0
                fina = None
                for p in poin:
                    #对所有满足条件的点，获取面积最小的那个作为最终的点
                    mianji = (p[2]-p[0])*(p[3]-p[1])
                    if ind == 0:
                        m = mianji
                    else:
                        if mianji>=m:
                            continue
                        else:
                            m = mianji    
                            fina = p
                    ind  += 1
                #获取到最终bounds
                print("found tuple point:")
                print(fina)
                
                i = wx.Bitmap(os.path.join(self.screenShotDir, "screenshot.png"))
                dc = wx.MemoryDC(i)
                dc.SetPen(wx.Pen(wx.RED, 1))
                #画矩形(wxpython里需要用drawline或drawlines, 因为drawrect是画实心矩形)
                dc.DrawLine(fina[0], fina[1], fina[0], fina[3])
                dc.DrawLine(fina[0], fina[1], fina[2], fina[1])
                dc.DrawLine(fina[2], fina[1], fina[2], fina[3])
                dc.DrawLine(fina[0], fina[3], fina[2], fina[3])
                dc.SelectObject(wx.NullBitmap)
                self.screenShot.SetBitmap(i)  
                i.SaveFile(os.path.join(self.screenShotDir, "screenshotDraw.png"), wx.BITMAP_TYPE_BMP)
                self.hasDrew = True
                #必须刷新panel，否则会出现上一次draw之后的残影
                self.Refresh(eraseBackground=True, rect=None)
                k = None
                for k in d:
                    if d[k] == fina:
                        print("found string point:")
                        print(k)
                        ind = 0
                        for v in treeDic.values(): 
                            if ind ==0:
                                pass
                            else:
                                b = v["bounds"]
                                if b == k:
                                    print("found node detail:")
                                    print(v)
                                    wx.CallAfter(pub.sendMessage, "setSelectedNode", msg = v)
                                    break
                            ind+=1
                        break
        else:
            msg = "请先获取页面截图和布局文件"
            print(msg)
            wx.CallAfter(pub.sendMessage, "update", msg=msg)
########################################################################
class RightTopPanel(scrolled.ScrolledPanel):
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        
        B = wx.StaticBox(self, -1)
        self.BSizer = wx.StaticBoxSizer(B, wx.VERTICAL)
        
        self.tree = XMLTree(parent=self, ID=-1)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelectItem)
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.getFullXpath)
        
        self.BSizer.Add(self.tree, 5, wx.EXPAND, 5)
        self.SetSizer(self.BSizer)
        cDir = os.getcwd()
        self.xmlPath = os.path.join(cDir,"Hierarchy","window_dump.xml")
        pub.subscribe(self.updateTree, "updateTree")
        pub.subscribe(self.setSelectedNode, "setSelectedNode")
        pub.subscribe(self.DoSearch, "DoSearch")
        
    def DoSearch(self, msg):
        if msg!="":
            try:
                #清除所有值钱设置的颜色，重新设置为黑色
                ind = 0
                for i in self.tree.ordeDic:
                    #不搜索根节点
                    if ind ==0:
                        pass
                    else:
                        self.tree.SetItemTextColour(i, "black")
                    ind += 1
                print("Doing search: %s" % msg)
                ind = 0
                fBreak = False
                #第一次遍历，搜到满足条件的节点后，就退出
                for i in self.tree.ordeDic:
                    #不搜索根节点
                    if ind ==0:
                        pass
                    else:
                        if not fBreak:
                            tt = self.tree.ordeDic[i].keys()
                            #搜索条件：class、text属性为包含，resource-id为完全匹配
                            for mm in ["class", "text", "resource-id"]:
                                if mm in tt:
                                    if mm=="class" or mm=="text":
                                        if  msg in self.tree.ordeDic[i][mm]:    
                                            self.tree.SelectItem(i, select=True)
                                            self.tree.SetItemTextColour(i, "red")
                                            fBreak = True
                                            break
                                    else:
                                        if  msg == self.tree.ordeDic[i][mm]:    
                                            self.tree.SelectItem(i, select=True)
                                            self.tree.SetItemTextColour(i, "red")
                                            fBreak = True
                                            break
                    ind += 1
                #第二次遍历，为了获取所有满足条件的结果数
                ind = 0
                searchResultCount = 0
                for i in self.tree.ordeDic:
                    #不搜索根节点
                    if ind ==0:
                        pass
                    else:
                        #搜索模式：class、text属性为包含，resource-id为完全匹配
                        tt = self.tree.ordeDic[i].keys()
                        #搜索条件：class、text属性为包含，resource-id为完全匹配
                        for mm in ["class", "text", "resource-id"]:
                            if mm in tt:
                                if mm=="class" or mm=="text":
                                    if  msg in self.tree.ordeDic[i][mm]: 
                                        searchResultCount+=1   
                                        if i!=self.tree.GetSelection():
                                            self.tree.SetItemTextColour(i,"green")
                                else:
                                    if  msg == self.tree.ordeDic[i][mm]:
                                        searchResultCount+=1    
                                        if i!=self.tree.GetSelection():
                                            self.tree.SetItemTextColour(i,"green")
                    ind+=1
                print("Search Complete")
                wx.CallAfter(pub.sendMessage, "updateSearchResultCount", msg = searchResultCount)
            except Exception as e:
                print("ERROR:",str(e))
            
    def getFullXpath(self, evt):
        fxpath = ""
        l = []
        it = evt.GetItem()
        l.append(it)
        p = self.tree.GetItemParent(it)
        while p!=self.tree.GetRootItem():
            l.append(p) 
            p = self.tree.GetItemParent(p)
        del l[-1]
        l.reverse()
        for i in l:
            xPath = self.tree.ordeDic[i]["class"]+"["+"@index="+"\'%s\'" % self.tree.ordeDic[i]["index"]+"]" 
            fxpath += "/"+xPath
    
        wx.CallAfter(pub.sendMessage, "updateXPath", msg=fxpath)
            
        
    def setSelectedNode(self, msg):
        for i in self.tree.ordeDic:
            if self.tree.ordeDic[i]==msg:
                self.tree.SelectItem(i, select=True)
                break
        
    def updateTree(self):
        self.tree.LoadTree(self.xmlPath)
        self.tree.ExpandAll()
        global treeDic
        treeDic = self.tree.ordeDic
        
    def onSelectItem(self, evt):
        item = evt.GetItem()
        if item!=self.tree.GetRootItem() and item!=self.tree.GetFirstChild(self.tree.GetRootItem()):
            global nodeDetailData
            nodeDetailData = self.tree.ordeDic[item]
            wx.CallAfter(pub.sendMessage, "updateNodeDetail")
            wx.CallAfter(pub.sendMessage,"DrawFromSelectedNode", msg = nodeDetailData["bounds"])

    
class RightBottomPanel(scrolled.ScrolledPanel):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.gd = GD.Grid(self) 
        self.gd.CreateGrid(20, 2) 
        self.gd.SetRowLabelSize(0)
        self.gd.SetColLabelSize(0)
        self.B = wx.StaticBox(self, -1, "Node Detail")
        BSizer = wx.StaticBoxSizer(self.B, wx.VERTICAL)
        BSizer.Add(self.gd, 1, wx.EXPAND|wx.ALL)
        
        self.SetSizer(BSizer)
        pub.subscribe(self.updateNodeDetail, "updateNodeDetail")
        pub.subscribe(self.updateXPath, "updateXPath")
        self.Bind(wx.EVT_SIZE, self.ResizeGrid)
    
    def updateXPath(self, msg):
        self.gd.SetCellValue(19, 0, "fullXPath")
        self.gd.SetCellValue(19, 1, "/"+msg)
        self.gd.Refresh(eraseBackground=True, rect=None)
        
    def updateNodeDetail(self):
        global nodeDetailData
        i = 0
        self.gd.ClearGrid()
        print(nodeDetailData)
        if nodeDetailData!=None:
            for j in nodeDetailData:
                try:
                    self.gd.SetCellValue(i, 0, j)
                    self.gd.SetCellValue(i, 1, nodeDetailData[j])
                    i += 1
                except:
                    print("更新节点具体信息失败"+str(i))
                    i += 1
            self.Refresh(eraseBackground=True, rect=None)
    
    def ResizeGrid(self, evt):
        siz = self.GetSize()
        if siz[0]>450:
            self.gd.SetColSize(1, siz[0]-100) 
########################################################################
class MainPanel(wx.Panel):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)
        self.imagesPath = os.path.join(".", "images")
        image_open_folder = wx.Image(os.path.join(self.imagesPath, "open-folder.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_screenShot = wx.Image(os.path.join(self.imagesPath, "screenshot.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_save = wx.Image(os.path.join(self.imagesPath, "save.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_rotate = wx.Image(os.path.join(self.imagesPath, "rotate.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_recorder = wx.Image(os.path.join(self.imagesPath, "recorder.jpg"), wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        image_exe = wx.Image(os.path.join(self.imagesPath, "go.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        topSizer = wx.GridSizer(1, 5, 5, 5)
        self.button_open_folder = wx.BitmapButton(self, -1, image_open_folder, size=(30,22))
        self.button_screenShot = wx.BitmapButton(self, -1, image_screenShot, size=(30,22))
        self.button_screenShot.SetToolTip("获取页面截图和布局文件")
        self.Bind(wx.EVT_BUTTON, self.updateScreenShot, self.button_screenShot)
        self.button_save = wx.BitmapButton(self, -1, image_save, size=(30,22))
        self.button_rotate = wx.BitmapButton(self, -1, image_rotate, size=(30, 22))
        self.Bind(wx.EVT_BUTTON, self.updateAfterRotate, self.button_rotate)
        self.exeButton = wx.BitmapButton(self, -1, image_exe, size=(30,22))
        self.exeButton.Bind(wx.EVT_BUTTON, self.tellToDoSwipeOrInput)
        self.exeButton.SetToolTip("执行动作")
        self.baseSettings = wx.StaticBox(self, -1, "基本操作")
        self.recordSettings = wx.StaticBox(self, -1, "同步操作")
        self.nodeSettings = wx.StaticBox(self, -1, "节点操作")
        self.operationParasSettings = wx.StaticBox(self, -1, "动作参数设置")
        self.searchBox = wx.TextCtrl(self, -1, size = (100,22))
        self.searchBtn = wx.Button(self, -1,  "搜索", size=(30,22))
        self.Bind(wx.EVT_BUTTON, self.tellToDoSearch, self.searchBtn)
        
        self.imagesPath = os.path.join(".", "images")  
        b1 = wx.StaticBoxSizer(self.baseSettings, wx.HORIZONTAL)
        b2 = wx.StaticBoxSizer(self.recordSettings, wx.HORIZONTAL)
        b3 = wx.StaticBoxSizer(self.nodeSettings, wx.HORIZONTAL)
        b3.Add(self.searchBox, 1, wx.ALL, 1)
        b3.Add(self.searchBtn, 1, wx.ALL, 1)
        
        self.inputB = wx.StaticBox(self, -1, "输入")
        inputBSizer = wx.StaticBoxSizer(self.inputB, wx.HORIZONTAL)
        b5 = wx.BoxSizer(wx.VERTICAL)
        self.inputContentText = wx.StaticText(self, -1,"内容:", size=(80,22))
        self.inputContent = wx.TextCtrl(self, -1, value=(""), size=(80,22))
        self.inputContent.SetToolTip("要对元素输入的内容")
        
        self.swipeB = wx.StaticBox(self, -1, "滑动")
        swipeBSizer = wx.StaticBoxSizer(self.swipeB, wx.HORIZONTAL)
        swipeBGSizer = wx.GridSizer(2,2,10,10)
        self.swipeStartX = IntC(self, -1, size = (40,22))
        self.swipeStartX.SetToolTip("滑动起始点横坐标")
        self.swipeStartY = IntC(self, -1, size = (40,22))
        self.swipeStartY.SetToolTip("滑动起始点纵坐标")
        self.swipeEndX = IntC(self, -1, size = (40,22))
        self.swipeEndX.SetToolTip("滑动终点横坐标")
        self.swipeEndY = IntC(self, -1, size = (40,22))
        self.swipeEndY.SetToolTip("滑动终点纵坐标")
        inputBSizer.Add(self.inputContentText, 1,wx.ALL,1)
        inputBSizer.Add(self.inputContent, 1,wx.ALL,1)
        
        swipeBGSizer.Add(self.swipeStartX, 5,wx.ALL,5)
        swipeBGSizer.Add(self.swipeStartY, 5,wx.ALL,5)
        swipeBGSizer.Add(self.swipeEndX, 5,wx.ALL,5)
        swipeBGSizer.Add(self.swipeEndY, 5,wx.ALL,5)
        swipeBSizer.Add(swipeBGSizer,10,wx.ALL|wx.EXPAND,5)
        b5.Add(inputBSizer)
        b5.Add(swipeBSizer,5,wx.EXPAND)
        
        b4 = wx.StaticBoxSizer(self.operationParasSettings, wx.HORIZONTAL)
        b4.Add(b5, 1, wx.ALL, 1)
        
        timeOutList = ["5", "6", "7", "8", "9", "10","11", "12", "13", "14", "15"]
        self.recordTimeOut = wx.ComboBox(self, -1, value="10",choices =  timeOutList,size=(40,20), style = wx.CB_READONLY)
        self.recordTimeOut.SetToolTip("重新获取页面截图和布局的延时时间")
        self.button_recorder = wx.BitmapButton(self, -1, image_recorder, size=(30,22)) 
        self.button_recorder.SetToolTip("开启/关闭同步模式")
        
        self.keyboardType = wx.ComboBox(self, -1, value="ADB",size = (60,22), choices=["ADB", "ORG"], style = wx.CB_READONLY)
        self.keyboardType.SetToolTip("键盘类型. 输入中文，选择ADB；输入英文或密码时，使用ORG")
        self.Bind(wx.EVT_BUTTON, self.updateRecordModel, self.button_recorder)
        b1.Add(self.button_open_folder, 1, wx.ALL, 1)
        b1.Add(self.button_screenShot, 1, wx.ALL, 1)
        b1.Add(self.button_save, 1, wx.ALL, 1)
        b1.Add(self.button_rotate, 1, wx.ALL, 1)
        b2.Add(self.recordTimeOut, 1, wx.ALL, 1)
        b2.Add(self.button_recorder, 1, wx.ALL, 1)
        b2.Add(self.keyboardType, 1, wx.ALL, 1)
        b2.Add(self.exeButton, 1, wx.ALL, 1)
        
        opeartionList = ["输入", "滑动"]
        self.OpeartionBox = wx.RadioBox(self, label = '动作', pos = (80,10), choices = opeartionList,majorDimension = 1, style = wx.RA_SPECIFY_ROWS) 
        self.OpeartionBox.Bind(wx.EVT_RADIOBOX,self.onClickOpeartionOption)
        
        topSizer.Add(b1, 1, wx.ALL, 1)
        topSizer.Add(b2, 1, wx.ALL, 1)
        topSizer.Add(self.OpeartionBox, 1, wx.ALL, 1)
        topSizer.Add(b4, 1, wx.ALL, 1)
        topSizer.Add(b3, 1, wx.ALL, 1)
        
        hSplitter = wx.SplitterWindow(self, style = wx.BORDER_SUNKEN)
        rSplitter = wx.SplitterWindow(hSplitter, style = wx.BORDER_SUNKEN)
 
        rTP = RightTopPanel(rSplitter)
        rBP = RightBottomPanel(rSplitter)
        rSplitter.SplitHorizontally(rTP, rBP)
        rSplitter.SetSashGravity(0.5)
 
        lP = LeftPanel(hSplitter)
        hSplitter.SplitVertically(lP,rSplitter )
        hSplitter.SetSashGravity(0.5)
 
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topSizer,1, wx.ALL|wx.EXPAND, 1)
        sizer.Add(hSplitter, 1, wx.EXPAND)

        self.SetSizer(sizer)
        pub.subscribe(self.updateSearchResultCount, "updateSearchResultCount")
    
    def tellToDoSwipeOrInput(self, evt):
        operationString = self.OpeartionBox.GetStringSelection()    
        inputC = self.inputContent.GetValue()
        sX = self.swipeStartX.GetValue()
        sY = self.swipeStartY.GetValue()
        eX = self.swipeEndX.GetValue()
        eY = self.swipeEndY.GetValue()        
        
        if operationString=="输入":
            if inputC=="":
                dlg = wx.MessageDialog(self, u"请检查输入内容", u"输入内容不能为空", wx.OK | wx.ICON_ERROR)
                if dlg.ShowModal() == wx.ID_OK:
                    dlg.Destroy()
            else:
                keyb = self.keyboardType.GetValue()
                wx.CallAfter(pub.sendMessage, "DoSwipeOrInput", msg =inputC+"\n"+keyb)
        else:
            if sX=="" or sY=="" or eX=="" or eY=="":
                dlg = wx.MessageDialog(self, u"请检查滑动坐标设置", u"滑动起始点和终点的横纵坐标均不能为空", wx.OK | wx.ICON_ERROR)
                if dlg.ShowModal() == wx.ID_OK:
                    dlg.Destroy()
            else:
                wx.CallAfter(pub.sendMessage, "DoSwipeOrInput", msg ="滑动\n%d\n%d\n%d\n%d" % (sX,sY,eX,eY))

    def updateAfterRotate(self,evt):
        screenShotPath = os.path.join(os.getcwd(), "screenShot", "screenshot.png")
        img = Image.open(screenShotPath)
        out = img.rotate(90,expand=1)
        out.save(screenShotPath)
        wx.CallAfter(pub.sendMessage, "update", msg=screenShotPath)

    def onClickOpeartionOption(self, evt):
        print(self.OpeartionBox.GetStringSelection(),' is clicked from Radio Box')
        
    def tellToDoSearch(self,evt):
        searchContent = self.searchBox.GetValue()
        wx.CallAfter(pub.sendMessage, "DoSearch", msg=searchContent)
        
    def updateScreenShot(self, evt):
        getNewScreenShotAndDomFileThread()

    def updateRecordModel(self, evt):
        global recordStatus
        if recordStatus == "关":
            dlg = wx.MessageDialog(self, u"1. 同步模式下，将不能通过点击页面来定位元素;\n2. 同步模式下将对页面进行模拟人工操作，并生成脚本;\n3. 同步完成后，请关闭同步模式。", u"确定进入同步模式?", wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                recordStatus="开"
                global recordTimeDelay
                recordTimeDelay = int(self.recordTimeOut.GetValue())
                print("当前设置同步超时为：", recordTimeDelay)
            dlg.Destroy() 
        else:
            recordStatus="关"
        self.Parent.updateRecordStatus(recordStatus)
    
    def updateSearchResultCount(self, msg):
        self.Parent.updateSearchResultCount(msg)
        
        
########################################################################            
class MyForm(wx.Frame):
 
    #----------------------------------------------------------------------
    def __init__(self):
        screenSize = wx.DisplaySize()
        x = screenSize[0]
        y = screenSize[1]-80
        wx.Frame.__init__(self, None, title="App Auto Viewer",
                          size=(x-80,y))
        self.panel = MainPanel(self)
        self.statusB = self.CreateStatusBar(number=2)
        global recordStatus
        recordStatus = "关"
        self.updateRecordStatus(recordStatus)
        self.statusB.SetStatusText("共找到    个结果", 1)
        
    def updateRecordStatus(self, model):
        self.statusB.SetStatusText("同步模式：%s" % model, 0)
        
    def updateSearchResultCount(self, c):
        self.statusB.SetStatusText("共找到  %d 个结果" % c, 1)
#----------------------------------------------------------------------
# Run the program
if __name__ == "__main__":
    app = wx.App(False)
    frame = MyForm()
    frame.Center()
    frame.Show()
    app.MainLoop()
    
