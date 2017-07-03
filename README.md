# AppAutoViewer
Compared to Google Android SDK uiautomatorviewer, easier to get full-Xpath, and support sync with Device.

required: Python3.6.1 64bit, wxpython 4.0.0a4.dev3153+ec9d660-cp36-cp36m-win_amd64, android SDK, windows 7/10

run: use any python IDE to open the project dir, and run UI.py or directly open command line, cd to the project dir and run 'python UI.py'.


用法：
基本用法与google原生uiautomatorviewer一样


其他：
1）搜索支持搜索元素的class属性，text属性，resource-id属性，前两者只要包含属性包含搜索内容就会被搜索到，最后者需要完全匹配才会搜索到；

2）获取完整的xpath路径：先选中某个节点，然后右键单击一次该节点，在右下方的面板中，就会显示出该节点的fullXPath

3）同步模式：同步模式下，将不再支持元素定位，所有的事件均是对设备的操作（通过命令下发）。其中，点击动作，直接点击AppAutoViewer界面即可；输入/滑动动作需要先设置参数（输入的内容，滑动的坐标），在点击执行按钮（注意：如果是输入动作，需要设置键盘，默认是ADB键盘---支持输入中文，如果要输入密码或者英文，请切换到ORG再点执行）。每次动作完成，为了保证设备新的界面已经同步下来，需要设置一个操作延迟时间，默认是10秒，10秒之后，提示信息弹框会自动消失，中途如果确认已经加载完成，可以点击弹框中的按钮“确认已经加载完成，我要马上结束”或X按钮来关闭弹框，马上重新加载。
