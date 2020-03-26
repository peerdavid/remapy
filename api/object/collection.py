from api.object.item import Item

class Collection(Item):

    def __init__(self, entry, parent):
        super(Collection, self).__init__(entry, parent)
        pass

    def add_child(self, child: Item):
        self.children.append(child)
        self.state = Item.STATE_COLLECTION