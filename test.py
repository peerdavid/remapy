import tkinter
from tkinter import d

def drop(event):
    entry_sv.set(event.data)

root = TkinterDnD.Tk()
entry_sv = Tkinter.StringVar()
entry = Tkinter.Entry(root, textvar=entry_sv, width=80)
entry.pack(fill=Tkinter.X)
entry.drop_target_register(DND_FILES)
entry.dnd_bind('<<Drop>>', drop)
root.mainloop()