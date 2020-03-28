import numpy as np
import model.item
from model.item import Item


STATE_COLLECTION = 100

class Collection(Item):

    def __init__(self, entry, parent):
        super(Collection, self).__init__(entry, parent)
        self.state = STATE_COLLECTION
        pass


    def add_child(self, child: Item):
        self.children.append(child)
        child.add_state_listener(self.listen_child_state_change)


    def delete(self):
        
        for child in self.children:
            ok = child.delete()
            if not ok:
                return False

        ok = self.rm_client.delete_item(self.id, self.version)
        if ok:
            self._update_state(state=STATE_DELETED)
        return ok


    def _update_state(self, state):
        self.state = state
        self._update_state_listener()
    

    def get_exact_children_count(self):
        """ Returns exact number of children and children of children etc.
            and it counts itself.
        
            return: (num_documents, num_collections)
        """
        count = [0, 1]
        for child in self.children:
            if child.is_document:
                count[0] += 1
                continue
            child_count = child.get_exact_children_count()
            count = np.add(count, child_count)
            
        return count
    

    def is_parent_of(self, item):
        for child in self.children:
            if child.id == item.id:
                return True
            
            if child.is_parent_of(item):
                return True
        
        return False
    
    def listen_child_state_change(self, item):
        if item.state == model.item.STATE_DELETED:
            self.children.remove(item)