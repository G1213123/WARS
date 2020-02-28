import tkinter
from tkinter import filedialog


class SaveSetting( tkinter.Toplevel ):
    # Prompt for configuring save settings
    # Activate by 'Enter' button in Map Frame
    # Batch save:   Save all map markers to multiple csv files in the same folder
    #               Default save names 'Marker1.csv', 'Marker2.csv' ...
    #               Unlock folder name entry/browse option
    # Consolidate:  Combine all markers csv files into single csv file
    #               Default save name 'routes_consolidate.csv'
    #               Save path refers to the last marker csv file
    # Show Map: open a map for the logging the selected AOIs

    def __init__(self, default_save='', **kw):
        # Configure save popup dialogue
        super().__init__( **kw )
        # self = tkinter.Toplevel()
        self.geometry( "%dx%d%+d%+d" % (300, 200, 250, 125) )
        self.title( "Save" )

        # Return save setting as dict
        self.out = {}

        # batch save checkbox
        frm_a = tkinter.Frame( self, width=self.winfo_reqwidth(), height=50 )
        frm_a.pack()
        self.batch = tkinter.IntVar( value=1 )
        self.batch_box = tkinter.Checkbutton( frm_a, text='batch save', variable=self.batch, command=self.com )
        self.batch_box.pack()

        # consolidate markers checkbox
        frm_b = tkinter.Frame( self, width=self.winfo_reqwidth(), height=50 )
        frm_b.pack()
        self.consld = tkinter.IntVar( value=1 )
        consld_box = tkinter.Checkbutton( frm_b, text='consolidate markers', variable=self.consld )
        consld_box.pack()

        # show html map check box
        frm_c = tkinter.Frame( self, width=self.winfo_reqwidth(), height=50, bg='green' )
        frm_c.pack()
        self.showmap = tkinter.IntVar( value=0 )
        map_box = tkinter.Checkbutton( frm_c, text='show map file', variable=self.showmap )
        map_box.pack()

        # Browse folder dialogue button
        frm_d = tkinter.Frame( self, width=self.winfo_reqwidth(), height=50 )
        frm_d.pack()
        label = tkinter.Label( frm_d, text="Folder" )
        label.pack()
        self.dirname_box = tkinter.StringVar( value=default_save )
        self.textbox = tkinter.Entry( frm_d, textvariable=self.dirname_box, width=200, state='normal' )
        self.textbox.pack()
        browse = tkinter.Button( frm_d, text='Browse', command=self.browse_button )
        browse.pack()

        # Done button
        button = tkinter.Button( self, text="Done", command=self.done )
        button.pack()

        # Set popup focus and wait
        self.grab_set()
        self.wait_window()

    def browse_button(self):
        # file dialog prompt for file picking
        self.grab_release()
        dirname = filedialog.askdirectory()
        self.textbox.delete( 0, tkinter.END )
        self.textbox.insert( 0, dirname )
        self.grab_set()
        self.focus_force()

    def com(self):
        # activate and deactivate file path entry box
        if self.batch.get():
            self.textbox.config( state='normal' )
        else:
            self.textbox.config( state='disabled' )

    def done(self):
        # output settings
        self.out = {'batch': self.batch.get(), 'consld': self.consld.get(), 'dirname': self.textbox.get(),
                    'map': self.showmap.get()}
        self.destroy()
