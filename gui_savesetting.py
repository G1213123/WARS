import tkinter
from tkinter import filedialog


class savesetting( tkinter.Toplevel ):
    # Prompt for configuring save settings
    # Activate by 'Enter' button in Map Frame
    # Batch save:   Save all map markers to multiple csv files in the same folder
    #               Default save names 'Marker1.csv', 'Marker2.csv' ...
    #               Unlock folder name entry/browse option
    # Consolidate:  Combine all markers csv files into single csv file
    #               Default save name 'routes_consolidate.csv'
    #               Save path refers to the last marker csv file

    def __init__(self):
        # Configure save popup dialogue
        self.popup = tkinter.Toplevel()
        self.popup.geometry( "%dx%d%+d%+d" % (300, 200, 250, 125) )
        self.popup.title( "Save" )

        # Return save setting as dict
        self.out = {'batch': False, 'consld': False, 'dirname': ''}

        # batch save checkbox
        frmA = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50 )
        frmA.pack()
        self.batch = tkinter.IntVar( value=1 )
        self.batch_box = tkinter.Checkbutton( frmA, text='batch save', variable=self.batch, command=self.com )
        self.batch_box.pack()

        # consolidate markers checkbox
        frmB = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50 )
        frmB.pack()
        self.consld = tkinter.IntVar( value=1 )
        consld_box = tkinter.Checkbutton( frmB, text='consolidate markers', variable=self.consld )
        consld_box.pack()

        # show html map check box
        frmC = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50, bg='green' )
        frmC.pack()
        self.showmap = tkinter.IntVar( value=0 )
        map_box = tkinter.Checkbutton( frmC, text='show map file', variable=self.showmap )
        map_box.pack()

        # Browse folder dialogue button
        frmD = tkinter.Frame( self.popup, width=self.popup.winfo_reqwidth(), height=50 )
        frmD.pack()
        label = tkinter.Label( frmD, text="Folder" )
        label.pack()
        self.dirname = tkinter.StringVar()
        self.textbox = tkinter.Entry( frmD, textvariable=self.dirname, width=200, state='normal' )
        self.textbox.pack()
        browse = tkinter.Button( frmD, text='Browse', command=self.browse_button )
        browse.pack()

        # Done button
        button = tkinter.Button( self.popup, text="Done", command=self.done )
        button.pack()

        # Set popup focus and wait
        self.popup.grab_set()
        self.popup.wait_window()

    def browse_button(self):
        # file dialog prompt for file picking
        self.popup.grab_release()
        dirname = filedialog.askdirectory()
        self.dirname = dirname
        self.textbox.insert( 0, dirname )
        self.popup.grab_set()
        self.popup.focus_force()

    def com(self):
        # activiate and deactivate file path entry box
        if self.batch.get():
            self.textbox.config( state='normal' )
        else:
            self.textbox.config( state='disabled' )

    def done(self):
        # output settings
        self.out = {'batch': self.batch.get(), 'consld': self.consld.get(), 'dirname': self.dirname,
                    'map': self.showmap.get()}
        self.popup.destroy()
