import  wx
from xml.parsers import expat

#----------------------------------------------------------------------

class XMLTree(wx.TreeCtrl):
    def __init__(self, parent, ID):
        wx.TreeCtrl.__init__(self, parent, ID)
        self._root = self.AddRoot("Root-No-Meaning")
        self.nodeStack = [self._root]
        self.ordeDic = {}
        
    def IsDescendant(self, firstItem, secondItem):
        "Recursive check if firstItem is a descendant of a secondItem."
        if firstItem == self._root:
            return False
        parentItem = self.GetItemParent(firstItem)
        if parentItem == secondItem:
            return True
        else:
            return self.IsDescendant(parentItem, secondItem)

    # Define a handler for start element events
    def StartElement(self, name, attrs ):
        try:
            name = attrs["class"]
        except:
            name = ""
        eid = self.AppendItem(self.nodeStack[-1], name)
        self.ordeDic[eid] = attrs
        self.nodeStack.append(eid)

    def EndElement(self,  name ):
        self.nodeStack = self.nodeStack[:-1]

    def CharacterData(self, data ):
        if data.strip():
            data = data.encode()
            self.AppendItem(self.nodeStack[-1], data)


    def LoadTree(self, filename):
        # Create a parser
        # 每次Load数据时，清空前一次的数据
        self.DeleteAllItems()
        self._root = self.AddRoot("Root-No-Meaning")
        self.nodeStack = [self._root]
        self.ordeDic = {}
        
        Parser = expat.ParserCreate()

        # Tell the parser what the start element handler is
        Parser.StartElementHandler = self.StartElement
        Parser.EndElementHandler = self.EndElement
        Parser.CharacterDataHandler = self.CharacterData

        # Parse the XML File，必须以二进制读，否则中文会解析不出来而报错
        Parser.Parse(open(filename,'rb').read(), 1)
    
    


