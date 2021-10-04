import os
import pickle
import tkinter
from tkinter import filedialog

from app import gui_logging

DIRECTORY = os.path.expanduser('~/Documents/Python_Scripts/WARS/cfg')
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)


class SaveSetting(tkinter.Toplevel):
    """    # Prompt for configuring save settings
            # Activate by 'Enter' button in Map Frame
            # Batch save:   Save all map markers to multiple csv files in the same folder
            #               Default save names 'Marker1.csv', 'Marker2.csv' ...
            #               Unlock folder name entry/browse option
            # Consolidate:  Combine all markers csv files into single csv file
            #               Default save name 'routes_consolidate.csv'
            #               Save path refers to the last marker csv file
            # Show Map: open the saved map for the record the selected AOIs                            """

    def __init__(self, default_save='', aoi_nos=1, **kw):
        # Configure save popup dialogue
        super().__init__(**kw)
        # self = tkinter.Toplevel()
        self.geometry("%dx%d%+d%+d" % (300, 200, 250, 125))
        self.name = 'save_cfg'
        self.title(self.name)
        self.aoi_nos = aoi_nos

        # create save config file directory
        self.savename = DIRECTORY + r'/save.cfg'
        self.__modules = [self]  # declare self as the only module for save setting logging

        # load previous settings, if not exist, load default settings
        self.out = {'batch': 1, 'consld': 1, 'dirname': '',
                    'showmap': 0, 'done': 0}
        try:
            self.preload()
        except FileNotFoundError:
            pass

        # batch save checkbox
        frm_a = tkinter.Frame(self, width=self.winfo_reqwidth(), height=50)
        frm_a.pack()
        self.tkv_batch = tkinter.IntVar(value=self.out['batch'])
        self.tk_batch_box = tkinter.Checkbutton(frm_a, text='Auto Files Naming', variable=self.tkv_batch,
                                                command=self.com)
        self.tk_batch_box.pack()

        # consolidate markers checkbox
        frm_b = tkinter.Frame(self, width=self.winfo_reqwidth(), height=50)
        frm_b.pack()
        self.tkv_consld = tkinter.IntVar(value=self.out['consld'])
        tk_consld_box = tkinter.Checkbutton(frm_b, text='Summarise all markers', variable=self.tkv_consld)
        if self.aoi_nos <= 2:
            tk_consld_box.config(state=tkinter.DISABLED)
            self.tkv_consld.set(0)
        tk_consld_box.pack()

        # show html map check box
        frm_c = tkinter.Frame(self, width=self.winfo_reqwidth(), height=50, bg='green')
        frm_c.pack()
        self.tkv_showmap = tkinter.IntVar(value=self.out['showmap'])
        tk_map_box = tkinter.Checkbutton(frm_c, text='show map file', variable=self.tkv_showmap)
        tk_map_box.pack()

        # Browse folder dialogue button
        frm_d = tkinter.Frame(self, width=self.winfo_reqwidth(), height=50)
        frm_d.pack()
        label = tkinter.Label(frm_d, text="Folder")
        label.pack()
        self.tkv_dirname_box = tkinter.StringVar(value=self.out['dirname'])
        self.tk_textbox = tkinter.Entry(frm_d, textvariable=self.tkv_dirname_box, width=200, state='normal')
        self.tk_textbox.pack()
        tk_browse = tkinter.Button(frm_d, text='Browse', command=self.browse_button)
        tk_browse.pack()

        # Done button
        button = tkinter.Button(self, text="Done", command=self.done)
        button.pack()

        # Listen done button click
        self.out['done'] = 0

        # Set popup focus and wait
        self.grab_set()
        self.wait_window()

    def browse_button(self):
        # file dialog prompt for file picking
        self.grab_release()
        dirname = filedialog.askdirectory()
        self.tk_textbox.delete(0, tkinter.END)
        self.tk_textbox.insert(0, dirname)
        self.grab_set()
        self.focus_force()

    def com(self):
        # activate and deactivate file path entry box
        if self.tkv_batch.get():
            self.tk_textbox.config(state='normal')
        else:
            self.tk_textbox.config(state='disabled')

    def done(self):
        # output settings
        self.out = {'batch': self.tkv_batch.get(), 'consld': self.tkv_consld.get(), 'dirname': self.tk_textbox.get(),
                    'showmap': self.tkv_showmap.get(), 'done': 1}
        save_settings = gui_logging.var_logging(self.__modules)

        # Create the file if it does not exist
        with open(self.savename, 'wb') as handle:
            pickle.dump(save_settings, handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.destroy()

    def preload(self):
        with open(self.savename, 'rb') as handle:
            save_settings = pickle.load(handle)
        for module in self.__modules:
            for key, value in save_settings[module.name].items():
                if key != 'aoi_nos':
                    setattr(module, key, value)

    def load_api(self):
        savename = os.path.expanduser('~/Documents/Python_Scripts/WARS/cfg/api.cfg')
        try:
            with open(savename, 'rb') as handle:
                self.api = pickle.load(handle)
        except (OSError, IOError) as e:
            return 1
        return 0
