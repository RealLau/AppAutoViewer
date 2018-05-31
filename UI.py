from __future__ import division
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
from Helper.Common import *

recordStatus = None
recordTimeDelay = None
nodeDetailData = None
tree_info = None
isDoingRecording = False
resize_percent = None


class GetNewScreenShotAndDomFileThread(Thread):
    def __init__(self, size):
        # 线程实例化时立即启动
        self.size = size
        Thread.__init__(self)
        self.start()

    def run(self):
        try:
            os.remove(os.path.join(os.getcwd(), "Hierarchy", "window_dump.xml"))
        except:
            pass
        # 获取设备连接信息，页面截图，以及布局文件
        wx.CallAfter(pub.sendMessage, "update", msg=u"获取设备信息中……")
        # 获取设备信息
        p = subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate(timeout=10)[0].decode()
        device_status = check_device(out)
        if device_status:
            p = subprocess.Popen("adb shell dumpsys window displays |head -n 3", shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out = p.communicate(timeout=10)[0].decode()
            display_info = get_android_display_info(out)
            wx.CallAfter(pub.sendMessage, "update", msg=u"当前安卓设备分辨率: %dx%d" % (display_info[0], display_info[1]))
            print("当前安卓设备分辨率: %dx%d" % (display_info[0], display_info[1]))
            msg = "获取设备信息成功"
            wx.CallAfter(pub.sendMessage, "update", msg=msg)
            # 获取页面截图文件
            wx.CallAfter(pub.sendMessage, "update", msg=u"获取页面截图中……")
            print(msg)
            print("获取页面截图中……")
            p = subprocess.Popen("adb shell /system/bin/screencap -p /sdcard/screenshot.png", shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.communicate(timeout=10)
            out_put = (out[0].decode() + out[1].decode()).replace("\r", "").replace("\n", "")
            if "error" in out_put:
                msg = "获取页面截图失败: " + out_put
                wx.CallAfter(pub.sendMessage, "update", msg=msg)
                print(msg)
                return
            else:
                msg = "获取页面截图成功"
                wx.CallAfter(pub.sendMessage, "update", msg=msg)
                print(msg)
                # 上传截图文件至PC：当前目录的screenShot下
                wx.CallAfter(pub.sendMessage, "update", msg="上传页面截图至PC……")
                cDir = os.getcwd()
                screenShotPath = os.path.join(cDir, "screenShot", "screenshot.png")
                p = subprocess.Popen("adb pull /sdcard/screenshot.png %s" % screenShotPath, shell=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out = p.communicate(timeout=10)
                out_put = (out[0].decode() + out[1].decode()).replace("\r", "").replace("\n", "")
                if "error" in out_put:
                    msg = "上传页面截图至PC失败: " + out_put
                    print(msg)
                    return
                else:
                    msg = "上传页面截图至PC成功"
                    print(msg)
                    wx.CallAfter(pub.sendMessage, "update", msg=msg)
                    im = Image.open(screenShotPath)
                    thumbnail = im.resize(self.size, Image.ANTIALIAS)
                    thumbnail_screenshots_path = os.path.join(cDir, "screenShot", "thumbnail_screenshot.png")
                    thumbnail.save(thumbnail_screenshots_path, quality=95)
                    wx.CallAfter(pub.sendMessage, "update", msg=thumbnail_screenshots_path)
                    # 获取页面布局文件adb shell uiautomator dump /mnt/sdcard/window_dump.xml  获得手机当前界面的UI信息，生成window_dump.xml
                    msg = "获取页面布局文件中……"
                    print(msg)
                    wx.CallAfter(pub.sendMessage, "update", msg=msg)
                    p = subprocess.Popen("adb shell uiautomator dump /sdcard/window_dump.xml", shell=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = p.communicate(timeout=20)
                    out_put = (out[0].decode() + out[1].decode()).replace("\r", "").replace("\n", "")
                    if "error" in out_put or "ERROR" in out_put:
                        msg = "获取页面布局文件失败: " + out_put + "动态页面不支持获取（建议：暂停播放后重试）"
                        print(msg)
                        wx.CallAfter(pub.sendMessage, "update", msg=msg)
                    else:
                        msg = "获取页面布局文件成功"
                        print(msg)
                        wx.CallAfter(pub.sendMessage, "update", msg=msg)
                        # 上传页面布局文件至PC：当前目录的Hierarchy下
                        print("上传页面布局文件至PC……")
                        wx.CallAfter(pub.sendMessage, "update", msg="上传页面布局文件至PC……")
                        xmlHierarchyPath = os.path.join(cDir, "Hierarchy", "window_dump.xml")
                        p = subprocess.Popen("adb pull /sdcard/window_dump.xml %s" % xmlHierarchyPath, shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out = p.communicate(timeout=20)
                        out_put = (out[0].decode() + out[1].decode()).replace("\r", "").replace("\n", "")
                        if "error" in out_put:
                            msg = "上传页面布局文件至PC失败: " + out_put
                            print(msg)
                            wx.CallAfter(pub.sendMessage, "update", msg=msg)
                            return
                        else:
                            msg = "上传页面布局文件至PC成功"
                            wx.CallAfter(pub.sendMessage, "update", msg=msg)
                            wx.CallAfter(pub.sendMessage, "update", msg=xmlHierarchyPath)
                            wx.CallAfter(pub.sendMessage, "updateTree")
                            print(msg)
                            wx.CallAfter(pub.sendMessage, "updateNodeDetail")
        else:
            msg = "获取设备信息失败: 请确认安卓设备与PC连接良好后重试"
            wx.CallAfter(pub.sendMessage, "update", msg=msg)
            print(msg)
            return


class BottomLeftPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        self.notUseDetaul = None
        wx.Panel.__init__(self, parent=parent)
        BSizer = wx.BoxSizer(wx.VERTICAL)
        self.imagesDir = os.path.join(".", "images")
        self.screenShotDir = os.path.join(".", "screenShot")
        self.defaultScreenShotImage = wx.Image(os.path.join(self.imagesDir, "default.png"),
                                               wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.screenShot = wx.StaticBitmap(self, -1, self.defaultScreenShotImage)
        self.screenShot.Bind(wx.EVT_LEFT_DOWN, self.draw_or_reload_all)
        self.statusBar = wx.StaticText(self, -1, "")
        BSizer.Add(self.statusBar)
        BSizer.Add(self.screenShot, proportion=0, flag=wx.ALL, border=10)
        self.SetSizer(BSizer)
        pub.subscribe(self.update_status, "update")
        pub.subscribe(self.draw_from_selected_node, "DrawFromSelectedNode")
        pub.subscribe(self.do_swipe_or_input, "DoSwipeOrInput")
        self.hasDrew = False
        self.Fit()

    def draw_from_selected_node(self, msg):
        print("Left Panel Size:", self.GetSize(), self.statusBar.GetSize())
        t = msg.replace("][", ",").replace("[", "").replace("]", "").split(",")
        global resize_percent
        osx = int(t[0]) / resize_percent[0]
        osy = int(t[1]) / resize_percent[1]
        oex = int(t[2]) / resize_percent[0]
        oey = int(t[3]) / resize_percent[1]
        i = wx.Bitmap(os.path.join(self.screenShotDir, "thumbnail_screenshot.png"))
        dc = wx.MemoryDC(i)
        dc.SetPen(wx.Pen(wx.RED, 1))
        # 画矩形(wxpython里需要用drawline或drawlines, 因为drawrect是画实心矩形)
        dc.DrawLine(osx, osy, osx, oey)
        dc.DrawLine(osx, osy, oex, osy)
        dc.DrawLine(oex, osy, oex, oey)
        dc.DrawLine(osx, oey, oex, oey)
        dc.SelectObject(wx.NullBitmap)
        self.screenShot.SetBitmap(i)
        self.Refresh(eraseBackground=True, rect=None)

    def clear_screen_shot(self, bmp):
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetBackground(wx.Brush("white"))
        dc.Clear()

    def update_status(self, msg):
        if os.path.isfile(msg):
            if ".png" in msg:
                self.clear_screen_shot(self.defaultScreenShotImage)
                orginal_screenshots = os.path.join(self.screenShotDir, "screenshot.png")
                orginal_screenshots_size = wx.Bitmap(orginal_screenshots).GetSize()
                thumbnail_screenshots_path = os.path.join(self.screenShotDir, "thumbnail_screenshot.png")
                self.thumbnail_screenshots = wx.Bitmap(thumbnail_screenshots_path)
                thumbnail_screenshots_size = self.thumbnail_screenshots.GetSize()
                global resize_percent
                resize_percent = orginal_screenshots_size[0] / thumbnail_screenshots_size[0], orginal_screenshots_size[
                    1] / thumbnail_screenshots_size[1]
                print("获取的截屏大小：", orginal_screenshots_size, "当前缩放为: ", thumbnail_screenshots_size, "缩放率: ",
                      resize_percent)
                self.screenShot.SetBitmap(self.thumbnail_screenshots)
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

    def do_swipe_or_input(self, msg):
        global recordStatus
        global tree_info
        global recordTimeDelay
        if tree_info:
            if recordStatus == "开":
                if "滑动" in msg:
                    d = msg.replace("滑动\n", "").split("\n")
                    print("命令：滑动,", "移动点: ", d)
                    os.system("adb shell input swipe %d %d %d %d" % (int(d[0]), int(d[1]), int(d[2]), int(d[3])))

                    dlg = MessageDialog('等待新的页面加载完成(已设置延时%d秒)' % recordTimeDelay, '提示')
                    wx.CallLater(recordTimeDelay * 1000, dlg.Destroy)
                    dlg.ShowModal()
                    current_panel_size = self.GetSize()
                    current_status_bar_size = self.statusBar.GetSize()
                    current_fit_size = current_panel_size[0] - 20, current_panel_size[1] - current_status_bar_size[
                        1] - 20
                    GetNewScreenShotAndDomFileThread(current_fit_size)
                else:
                    if check_adb_keyboard_installed() and set_current_input_method():
                        c = msg.split("\n")[0]
                        kT = msg.split("\n")[1]
                        print("命令：输入,", "内容：", c)
                        if c != '':
                            if kT == "ADB":
                                os.system("adb shell am broadcast -a ADB_INPUT_TEXT --es msg '%s'" % c)
                            else:
                                os.system("adb shell input text '%s'" % c)

                            dlg = MessageDialog('等待新的页面加载完成(已设置延时%d秒)' % recordTimeDelay, '提示')
                            wx.CallLater(recordTimeDelay * 1000, dlg.Destroy)
                            dlg.ShowModal()
                            current_panel_size = self.GetSize()
                            current_status_bar_size = self.statusBar.GetSize()
                            current_fit_size = current_panel_size[0] - 20, current_panel_size[1] - current_status_bar_size[
                                1] - 20
                            GetNewScreenShotAndDomFileThread(current_fit_size)
                        else:
                            dlg = wx.MessageDialog(self, u"请检查输入内容", u"输入内容不能为空", wx.OK | wx.ICON_ERROR)
                            if dlg.ShowModal() == wx.ID_OK:
                                dlg.Destroy()
                    else:
                        dlg = wx.MessageDialog(self, u"ADB Keyboard未安装或未启用: https://github.com/senzhk/ADBKeyBoard/blob/758dab32cb220ffbf4bd1a2a58338c8948c86a63/bin/ADBKeyBoard.apk", u"请检查ADB Keyboard", wx.OK | wx.ICON_ERROR)
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

    def draw_or_reload_all(self, e):
        pos = e.GetPosition()
        print("detected click point:")
        global resize_percent
        x = (pos[0] - 10) * resize_percent[0]
        y = (pos[1] - 10) * resize_percent[1]
        print(x, y)
        global tree_info
        if tree_info:
            global recordStatus
            if recordStatus == "开":
                print("命令：点击", (x, y))
                os.system("adb shell input tap %d %d" % (x, y))
                global recordTimeDelay
                dlg = MessageDialog('等待新的页面加载完成(已设置延时%d秒)' % recordTimeDelay, '提示')
                wx.CallLater(recordTimeDelay * 1000, dlg.Destroy)
                dlg.ShowModal()
                current_panel_size = self.GetSize()
                current_status_bar_size = self.statusBar.GetSize()
                current_fit_size = current_panel_size[0] - 20, current_panel_size[1] - current_status_bar_size[1] - 20
                GetNewScreenShotAndDomFileThread(current_fit_size)
            else:

                ind = 0
                d = OrderedDict()
                poin = []
                # 找出被点击的点所在的最小矩形(该矩形对应节点的bounds属性)
                for v in tree_info.values():
                    # 根节点：{'rotation':1}不管
                    if ind == 0:
                        pass
                    else:
                        b = v["bounds"]
                        t = b.replace("][", ",").replace("[", "").replace("]", "").split(",")
                        osx = int(t[0])
                        osy = int(t[1])
                        oex = int(t[2])
                        oey = int(t[3])
                        if x > osx and y > osy and x < oex and y < oey:
                            poin.append((osx, osy, oex, oey))
                            d[b] = (osx, osy, oex, oey)
                    ind += 1
                m = 0
                ind = 0
                fina = None
                for p in poin:
                    # 对所有满足条件的点，获取面积最小的那个作为最终的点
                    mianji = (p[2] - p[0]) * (p[3] - p[1])
                    if ind == 0:
                        m = mianji
                    else:
                        if mianji >= m:
                            continue
                        else:
                            m = mianji
                            fina = p
                    ind += 1
                # 获取到最终bounds
                print("found tuple point:")
                print(fina)

                i = wx.Bitmap(os.path.join(self.screenShotDir, "thumbnail_screenshot.png"))
                dc = wx.MemoryDC(i)
                dc.SetPen(wx.Pen(wx.RED, 1))
                # 画矩形(wxpython里需要用drawline或drawlines, 因为drawrect是画实心矩形)
                dc.DrawLine(fina[0] / resize_percent[0], fina[1] / resize_percent[1], fina[0] / resize_percent[0],
                            fina[3] / resize_percent[1])
                dc.DrawLine(fina[0] / resize_percent[0], fina[1] / resize_percent[1], fina[2] / resize_percent[0],
                            fina[1] / resize_percent[1])
                dc.DrawLine(fina[2] / resize_percent[0], fina[1] / resize_percent[1], fina[2] / resize_percent[0],
                            fina[3] / resize_percent[1])
                dc.DrawLine(fina[0] / resize_percent[0], fina[3] / resize_percent[1], fina[2] / resize_percent[0],
                            fina[3] / resize_percent[1])
                dc.SelectObject(wx.NullBitmap)
                self.screenShot.SetBitmap(i)
                i.SaveFile(os.path.join(self.screenShotDir, "screenshotDraw.png"), wx.BITMAP_TYPE_BMP)
                self.hasDrew = True
                # 必须刷新panel，否则会出现上一次draw之后的残影
                self.Refresh(eraseBackground=True, rect=None)
                k = None
                for k in d:
                    if d[k] == fina:
                        print("found string point:")
                        print(k)
                        ind = 0
                        for v in tree_info.values():
                            if ind == 0:
                                pass
                            else:
                                b = v["bounds"]
                                if b == k:
                                    print("found node detail:")
                                    print(v)
                                    wx.CallAfter(pub.sendMessage, "setSelectedNode", msg=v)
                                    break
                            ind += 1
                        break
        else:
            msg = "请先获取页面截图和布局文件"
            print(msg)
            wx.CallAfter(pub.sendMessage, "update", msg=msg)


class BottomRightTopPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent=parent)

        B = wx.StaticBox(self, -1)
        self.BSizer = wx.StaticBoxSizer(B, wx.VERTICAL)

        self.tree = XMLTree(parent=self, ID=-1)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select_item)
        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.get_full_xpath)

        self.BSizer.Add(self.tree, 5, wx.EXPAND, 5)
        self.SetSizer(self.BSizer)
        self.SetMinSize(size=(100, 200))
        cDir = os.getcwd()
        self.xmlPath = os.path.join(cDir, "Hierarchy", "window_dump.xml")
        pub.subscribe(self.update_tree, "updateTree")
        pub.subscribe(self.set_selected_node, "setSelectedNode")
        pub.subscribe(self.do_search, "DoSearch")
        self.SetupScrolling()

    def do_search(self, msg):
        if msg != "":
            try:
                # 清除所有值钱设置的颜色，重新设置为黑色
                ind = 0
                for i in self.tree.ordeDic:
                    # 不搜索根节点
                    if ind == 0:
                        pass
                    else:
                        self.tree.SetItemTextColour(i, "black")
                    ind += 1
                print("Doing search: %s" % msg)
                ind = 0
                fBreak = False
                # 第一次遍历，搜到满足条件的节点后，就退出
                for i in self.tree.ordeDic:
                    # 不搜索根节点
                    if ind == 0:
                        pass
                    else:
                        if not fBreak:
                            tt = self.tree.ordeDic[i].keys()
                            # 搜索条件：class、text属性为包含，resource-id为完全匹配
                            for mm in ["class", "text", "resource-id"]:
                                if mm in tt:
                                    if mm == "class" or mm == "text":
                                        if msg in self.tree.ordeDic[i][mm]:
                                            self.tree.SelectItem(i, select=True)
                                            self.tree.SetItemTextColour(i, "red")
                                            fBreak = True
                                            break
                                    else:
                                        if msg == self.tree.ordeDic[i][mm]:
                                            self.tree.SelectItem(i, select=True)
                                            self.tree.SetItemTextColour(i, "red")
                                            fBreak = True
                                            break
                    ind += 1
                # 第二次遍历，为了获取所有满足条件的结果数
                ind = 0
                searchResultCount = 0
                for i in self.tree.ordeDic:
                    # 不搜索根节点
                    if ind == 0:
                        pass
                    else:
                        # 搜索模式：class、text属性为包含，resource-id为完全匹配
                        tt = self.tree.ordeDic[i].keys()
                        # 搜索条件：class、text属性为包含，resource-id为完全匹配
                        for mm in ["class", "text", "resource-id"]:
                            if mm in tt:
                                if mm == "class" or mm == "text":
                                    if msg in self.tree.ordeDic[i][mm]:
                                        searchResultCount += 1
                                        if i != self.tree.GetSelection():
                                            self.tree.SetItemTextColour(i, "green")
                                else:
                                    if msg == self.tree.ordeDic[i][mm]:
                                        searchResultCount += 1
                                        if i != self.tree.GetSelection():
                                            self.tree.SetItemTextColour(i, "green")
                    ind += 1
                print("Search Complete")
                wx.CallAfter(pub.sendMessage, "updateSearchResultCount", msg=searchResultCount)
            except Exception as e:
                print("ERROR:", str(e))

    def get_full_xpath(self, evt):
        fxpath = ""
        l = []
        it = evt.GetItem()
        l.append(it)
        p = self.tree.GetItemParent(it)
        while p != self.tree.GetRootItem():
            l.append(p)
            p = self.tree.GetItemParent(p)
        del l[-1]
        l.reverse()
        for i in l:
            xPath = self.tree.ordeDic[i]["class"] + "[" + "@index=" + "\'%s\'" % self.tree.ordeDic[i]["index"] + "]"
            fxpath += "/" + xPath

        wx.CallAfter(pub.sendMessage, "updateXPath", msg=fxpath)

    def set_selected_node(self, msg):
        for i in self.tree.ordeDic:
            if self.tree.ordeDic[i] == msg:
                self.tree.SelectItem(i, select=True)
                break

    def update_tree(self):
        self.tree.LoadTree(self.xmlPath)
        self.tree.ExpandAll()
        global tree_info
        tree_info = self.tree.ordeDic

    def on_select_item(self, evt):
        item = evt.GetItem()
        if item != self.tree.GetRootItem() and item != self.tree.GetFirstChild(self.tree.GetRootItem()):
            global nodeDetailData
            nodeDetailData = self.tree.ordeDic[item]
            wx.CallAfter(pub.sendMessage, "updateNodeDetail")
            wx.CallAfter(pub.sendMessage, "DrawFromSelectedNode", msg=nodeDetailData["bounds"])


class BottomRightBottomPanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        """Constructor"""
        scrolled.ScrolledPanel.__init__(self, parent=parent)
        self.gd = GD.Grid(self)
        self.gd.CreateGrid(20, 2)
        self.gd.SetRowLabelSize(0)
        self.gd.SetColLabelSize(0)
        self.B = wx.StaticBox(self, -1, "Node Detail")
        BSizer = wx.StaticBoxSizer(self.B, wx.VERTICAL)
        BSizer.Add(self.gd, 1, wx.EXPAND | wx.ALL)

        self.SetSizer(BSizer)
        self.Fit()
        pub.subscribe(self.update_node_detail, "updateNodeDetail")
        pub.subscribe(self.update_xpath, "updateXPath")
        self.Bind(wx.EVT_SIZE, self.resize_grid)
        self.SetupScrolling()

    def update_xpath(self, msg):
        self.gd.SetCellValue(19, 0, "fullXPath")
        self.gd.SetCellValue(19, 1, "/" + msg)
        self.gd.Refresh(eraseBackground=True, rect=None)

    def update_node_detail(self):
        global nodeDetailData
        i = 0
        self.gd.ClearGrid()
        print(nodeDetailData)
        if nodeDetailData:
            for j in nodeDetailData:
                try:
                    self.gd.SetCellValue(i, 0, j)
                    self.gd.SetCellValue(i, 1, nodeDetailData[j])
                    i += 1
                except:
                    print("更新节点具体信息失败" + str(i))
                    i += 1
            self.Refresh(eraseBackground=True, rect=None)

    def resize_grid(self, evt):
        siz = self.GetSize()
        if siz[0] > 450:
            self.gd.SetColSize(1, siz[0] - 100)


class TopPanel(wx.Panel):
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)
        self.imagesPath = os.path.join(".", "images")
        image_open_folder = wx.Image(os.path.join(self.imagesPath, "open-folder.png"),
                                     wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_screenShot = wx.Image(os.path.join(self.imagesPath, "screenshot.png"),
                                    wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_save = wx.Image(os.path.join(self.imagesPath, "save.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_rotate = wx.Image(os.path.join(self.imagesPath, "rotate.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        image_recorder = wx.Image(os.path.join(self.imagesPath, "recorder.jpg"), wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        image_exe = wx.Image(os.path.join(self.imagesPath, "go.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        topSizer = wx.GridSizer(1, 5, 1, 1)
        self.button_open_folder = wx.BitmapButton(self, -1, image_open_folder, size=(30, 22))
        self.button_screenShot = wx.BitmapButton(self, -1, image_screenShot, size=(30, 22))
        self.button_screenShot.SetToolTip("获取页面截图和布局文件")
        self.Bind(wx.EVT_BUTTON, self.update_screen_shot, self.button_screenShot)
        self.button_save = wx.BitmapButton(self, -1, image_save, size=(30, 22))
        self.button_rotate = wx.BitmapButton(self, -1, image_rotate, size=(30, 22))
        self.Bind(wx.EVT_BUTTON, self.update_after_rotate, self.button_rotate)
        self.exeButton = wx.BitmapButton(self, -1, image_exe, size=(30, 22))
        self.exeButton.Bind(wx.EVT_BUTTON, self.tell_to_do_swipe_or_input)
        self.exeButton.SetToolTip("执行动作")
        self.baseSettings = wx.StaticBox(self, -1, "基本操作")
        self.recordSettings = wx.StaticBox(self, -1, "同步操作")
        self.nodeSettings = wx.StaticBox(self, -1, "节点操作")
        self.operationParasSettings = wx.StaticBox(self, -1, "动作参数设置")
        self.searchBox = wx.TextCtrl(self, -1, size=(100, 22))
        self.searchBtn = wx.Button(self, -1, "搜索", size=(30, 22))
        self.Bind(wx.EVT_BUTTON, self.tell_to_do_search, self.searchBtn)
        b6 = wx.GridSizer(2, 2, 1, 1)
        self.imagesPath = os.path.join(".", "images")
        b1 = wx.StaticBoxSizer(self.baseSettings, wx.HORIZONTAL)
        b2 = wx.StaticBoxSizer(self.recordSettings, wx.HORIZONTAL)
        b3 = wx.StaticBoxSizer(self.nodeSettings, wx.HORIZONTAL)
        b3.Add(self.searchBox, 1, wx.ALL, 1)
        b3.Add(self.searchBtn, 1, wx.ALL, 1)

        self.inputB = wx.StaticBox(self, -1, "输入")
        inputBSizer = wx.StaticBoxSizer(self.inputB, wx.HORIZONTAL)
        b5 = wx.BoxSizer(wx.VERTICAL)
        self.inputContentText = wx.StaticText(self, -1, "内容:", size=(80, 22))
        self.inputContent = wx.TextCtrl(self, -1, value=(""), size=(80, 22))
        self.inputContent.SetToolTip("要对元素输入的内容")

        self.swipeB = wx.StaticBox(self, -1, "滑动")
        swipeBSizer = wx.StaticBoxSizer(self.swipeB, wx.HORIZONTAL)
        swipeBGSizer = wx.GridSizer(2, 2, 10, 10)
        self.swipeStartX = IntC(self, -1, size=(40, 22))
        self.swipeStartX.SetToolTip("滑动起始点横坐标")
        self.swipeStartY = IntC(self, -1, size=(40, 22))
        self.swipeStartY.SetToolTip("滑动起始点纵坐标")
        self.swipeEndX = IntC(self, -1, size=(40, 22))
        self.swipeEndX.SetToolTip("滑动终点横坐标")
        self.swipeEndY = IntC(self, -1, size=(40, 22))
        self.swipeEndY.SetToolTip("滑动终点纵坐标")
        inputBSizer.Add(self.inputContentText, 1, wx.ALL, 1)
        inputBSizer.Add(self.inputContent, 1, wx.ALL, 1)

        swipeBGSizer.Add(self.swipeStartX, 1, wx.ALL, 5)
        swipeBGSizer.Add(self.swipeStartY, 1, wx.ALL, 5)
        swipeBGSizer.Add(self.swipeEndX, 1, wx.ALL, 5)
        swipeBGSizer.Add(self.swipeEndY, 1, wx.ALL, 5)
        swipeBSizer.Add(swipeBGSizer, 1, wx.ALL | wx.EXPAND, 5)
        b5.Add(inputBSizer)
        b5.Add(swipeBSizer, 1, wx.EXPAND)

        b4 = wx.StaticBoxSizer(self.operationParasSettings, wx.HORIZONTAL)
        b4.Add(b5, 1, wx.ALL, 1)

        timeOutList = ["5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]
        self.recordTimeOut = wx.ComboBox(self, -1, value="10", choices=timeOutList, style=wx.CB_READONLY)
        self.recordTimeOut.SetToolTip("重新获取页面截图和布局的延时时间")
        self.button_recorder = wx.BitmapButton(self, -1, image_recorder)
        self.button_recorder.SetToolTip("开启/关闭同步模式")

        self.keyboardType = wx.ComboBox(self, -1, value="ADB", choices=["ADB", "ORG"], style=wx.CB_READONLY)
        self.keyboardType.SetToolTip("键盘类型. 输入中文，选择ADB；输入英文或密码时，使用ORG")
        self.Bind(wx.EVT_BUTTON, self.update_record_model, self.button_recorder)
        b1.Add(self.button_open_folder, 1, wx.ALL, 1)
        b1.Add(self.button_screenShot, 1, wx.ALL, 1)
        b1.Add(self.button_save, 1, wx.ALL, 1)
        b1.Add(self.button_rotate, 1, wx.ALL, 1)

        b6.Add(self.recordTimeOut, 1, wx.ALL, 1)
        b6.Add(self.button_recorder, 1, wx.ALL, 1)
        b6.Add(self.keyboardType, 1, wx.ALL, 1)
        b6.Add(self.exeButton, 1, wx.ALL, 1)
        b2.Add(b6)
        opeartionList = ["输入", "滑动"]
        self.OpeartionBox = wx.RadioBox(self, label='动作', choices=opeartionList, majorDimension=1,
                                        style=wx.RA_SPECIFY_ROWS)
        self.OpeartionBox.Bind(wx.EVT_RADIOBOX, self.on_click_operation_option)

        topSizer.Add(b1, 1, wx.EXPAND, 1)
        topSizer.Add(b2, 1, wx.EXPAND, 1)
        topSizer.Add(self.OpeartionBox, 1, wx.ALL, 1)
        topSizer.Add(b4, 1, wx.EXPAND, 1)
        topSizer.Add(b3, 1, wx.EXPAND, 1)
        self.SetSizer(topSizer)
        self.Fit()

    def tell_to_do_swipe_or_input(self, evt):
        operationString = self.OpeartionBox.GetStringSelection()
        inputC = self.inputContent.GetValue()
        sX = self.swipeStartX.GetValue()
        sY = self.swipeStartY.GetValue()
        eX = self.swipeEndX.GetValue()
        eY = self.swipeEndY.GetValue()

        if operationString == "输入":
            if not inputC:
                dlg = wx.MessageDialog(self, u"请检查输入内容", u"输入内容不能为空", wx.OK | wx.ICON_ERROR)
                if dlg.ShowModal() == wx.ID_OK:
                    dlg.Destroy()
            else:
                keyb = self.keyboardType.GetValue()

                wx.CallAfter(pub.sendMessage, "DoSwipeOrInput", msg=inputC + "\n" + keyb)
        else:
            if not sX or not sY or not eX or not eY:
                dlg = wx.MessageDialog(self, u"请检查滑动坐标设置", u"滑动起始点和终点的横纵坐标均不能为空", wx.OK | wx.ICON_ERROR)
                if dlg.ShowModal() == wx.ID_OK:
                    dlg.Destroy()
            else:
                wx.CallAfter(pub.sendMessage, "DoSwipeOrInput", msg="滑动\n%d\n%d\n%d\n%d" % (sX, sY, eX, eY))

    def update_after_rotate(self, evt):
        screenShotPath = os.path.join(os.getcwd(), "screenShot", "screenshot.png")
        img = Image.open(screenShotPath)
        out = img.rotate(90, expand=1)
        out.save(screenShotPath)
        wx.CallAfter(pub.sendMessage, "update", msg=screenShotPath)

    def on_click_operation_option(self, evt):
        print(self.OpeartionBox.GetStringSelection(), ' is clicked from Radio Box')

    def tell_to_do_search(self, evt):
        searchContent = self.searchBox.GetValue()
        wx.CallAfter(pub.sendMessage, "DoSearch", msg=searchContent)

    def update_screen_shot(self, evt):
        bottom_left_panel_size = self.Parent.Parent.bottom_left_panel.GetSize()
        bottom_left_panel_status_bar_size = self.Parent.Parent.bottom_left_panel.statusBar.GetSize()
        current_fit_size = bottom_left_panel_size[0] - 20, \
            bottom_left_panel_size[1] - bottom_left_panel_status_bar_size[1] - 20
        GetNewScreenShotAndDomFileThread(current_fit_size)

    def update_record_model(self, evt):
        global recordStatus
        if recordStatus == "关":
            dlg = wx.MessageDialog(self, u"1. 同步模式下，将不能通过点击页面来定位元素;\n2. 同步模式下将对页面进行模拟人工操作，并生成脚本;\n3. 同步完成后，请关闭同步模式。",
                                   u"确定进入同步模式?", wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                recordStatus = "开"
                global recordTimeDelay
                recordTimeDelay = int(self.recordTimeOut.GetValue())
                print("当前设置同步超时为：", recordTimeDelay)
            dlg.Destroy()
        else:
            recordStatus = "关"
        self.Parent.Parent.Parent.update_record_status(recordStatus)


class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        main_splitter = wx.SplitterWindow(self, style=wx.BORDER_SUNKEN)
        bottom_splitter = wx.SplitterWindow(main_splitter, style=wx.BORDER_SUNKEN)
        bottom_right_splitter = wx.SplitterWindow(bottom_splitter, style=wx.BORDER_SUNKEN)

        top_panel = TopPanel(main_splitter)
        main_splitter.SplitHorizontally(top_panel, bottom_splitter)

        bottom_right_top_panel = BottomRightTopPanel(bottom_right_splitter)
        bottom_right_bottom_panel = BottomRightBottomPanel(bottom_right_splitter)
        bottom_right_splitter.SplitHorizontally(bottom_right_top_panel, bottom_right_bottom_panel)

        self.bottom_left_panel = BottomLeftPanel(bottom_splitter)
        bottom_splitter.SplitVertically(self.bottom_left_panel, bottom_right_splitter)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(main_splitter, 1, wx.EXPAND, 1)
        self.SetSizerAndFit(sizer)
        pub.subscribe(self.update_search_result_count, "updateSearchResultCount")
        self.size = self.GetSize()
        self.bottom_left_panel.SetMinSize((self.size[0]/3, self.size[1]/3))

    def update_search_result_count(self, msg):
        self.Parent.update_search_result_count(msg)


class MyForm(wx.Frame):
    def __init__(self):
        screenSize = wx.DisplaySize()
        x = screenSize[0]
        y = screenSize[1] - 80
        wx.Frame.__init__(self, None, title="App Auto Viewer",
                          size=(x - 80, y))
        self.panel = MainPanel(self)
        self.statusB = self.CreateStatusBar(number=2)
        global recordStatus
        recordStatus = "关"
        self.update_record_status(recordStatus)
        self.statusB.SetStatusText("共找到    个结果", 1)

    def update_record_status(self, model):
        self.statusB.SetStatusText("同步模式：%s" % model, 0)

    def update_search_result_count(self, c):
        self.statusB.SetStatusText("共找到  %d 个结果" % c, 1)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MyForm()
    frame.Center()
    frame.Show()
    app.MainLoop()

