import tkinter as tk


# Credit: https://stackoverflow.com/questions/27820178/how-to-add-placeholder-to-an-entry-in-tkinter
class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="", color='grey', textvariable=None):
        super().__init__(master, textvariable=textvariable)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in_event_handler)
        self.bind("<FocusOut>", self.foc_out_event_handler)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in_event_handler(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out_event_handler(self, *args):
        if not self.get():
            self.put_placeholder()