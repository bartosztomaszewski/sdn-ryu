from Tkinter import *
import subprocess
import tkMessageBox as messagebox
import json

def add_host():  
    data = {}
    blocked_host = gui_text_add.get()
    try:
        with open("data.json", "r") as f:
            data = json.loads(f.read())

        with open ("data.json", "w") as f:
            data[blocked_host] = "10.0.0." + blocked_host[1:]
            json.dump(data, f)
            
    except IOError:
        with open ("data.json", "w") as f:
            data[blocked_host] = "10.0.0." + blocked_host[1:]
            json.dump(data, f)
        
    gui_labelbox.configure(text=blocked_host + " has been blocked")
    gui_messagebox.configure(text="")

    
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to stop RYU Controller?"):
        subprocess.Popen(["pkill", "-9", "ryu-manager"])
        gui_window.destroy()

def show_all():
    txt = ""
    try:
        with open('data.json', 'r') as f:
            data = json.loads(f.read())
            #lbl.configure(text=data)
            for key in data:
                txt = txt + key + " - " + data[key] + "\n"
            gui_messagebox.configure(text=txt)
    except IOError:
        gui_labelbox.configure(text="Nothing to block")

def remove_host():
    data = {}
    freed_host = gui_text_remove.get()
    try:
        with open("data.json", "r") as f:
            data = json.loads(f.read())
        
        if freed_host in data:
            del data[freed_host]
        
        with open ("data.json", "w") as f:
            #data[blocked_host] = "10.0.0." + blocked_host[1:]
            json.dump(data, f)
            
    except IOError:
        pass
    
    gui_labelbox.configure(text=freed_host + " is not blocked")
    gui_messagebox.configure(text="")

gui_window = Tk()
gui_window.title("RYU controller")
gui_window.geometry('550x400')

gui_button_add = Button(gui_window, width=20, text="Block host", command=add_host)
gui_button_add.grid(column=0, row=0)

gui_text_add = Entry(gui_window,width=10)
gui_text_add.grid(column=1, row=0)

gui_button_remove = Button(gui_window, width=20, text="Remove blockade", command=remove_host)
gui_button_remove.grid(column=0, row=1)

gui_text_remove = Entry(gui_window,width=10)
gui_text_remove.grid(column=1, row=1)

gui_button_show = Button(gui_window, width=20, text="Show blocked hosts", command=show_all)
gui_button_show.grid(column=0, row=2)

gui_labelbox = Label(gui_window, width=30)
gui_labelbox.grid(column=0, row=3)

gui_messagebox = Message(gui_window, width=300)
gui_messagebox.grid(column=0, row=4)

gui_button_quit = Button(gui_window, text="Quit", command=on_closing)
gui_button_quit.grid(column=1, row=5)

subprocess.Popen(["ryu-manager", "my_switch.py"])

gui_window.protocol("WM_DELETE_WINDOW", on_closing)
gui_window.mainloop()
