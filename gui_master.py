'''
Created on Jan 1, 2020

@author: Andrew.WF.Ng
'''

import os
import pickle
import tkinter
from tkinter import messagebox
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfile

import gui_frame_canvas
import gui_logging
from gui_headway import get_headway
from gui_routes import displayroutes


class MainWindow( tkinter.Toplevel ):
    """
    Mainwindow is the mother window for containing all the widgets.
    The direct child widgets are the file menu and tabs.
    Current build includes 4 tabs:
        Tab 1: Log
            --  For debuging usage. Displaying specify type of vatiables in remaining tab for their operation.
                Text structure please see pickle binary highest protocol
            Corresponding import: gui_logging
        Tab 2: Map
            --  Map interface for specifying the area of interest to scrap public transport routes.
            Corresponding import: gui_frame_canvas
        Tab 3: Routes
            --  A table for listing searched routes in the area
            Corresponding import: gui_routes
        Tab 4: Headway
            --  A table for displaying the headway data of the selected routes in Tab 3
            Corresponding import: gui_headway

    Local functions are for file menus and tabs operations.
    a
    """

    def save_as_work(self, saveas=None):
        """
        Save the current working space (including areas, drawing mode, service provider, routes and headway loaded)
            as standalone file

        Args:
            saveas (bool): if true ask for save file name else directly save with path previously specified by saveas
        """
        ftypes = [('Workspace Save', '.wsv')]
        if saveas:
            tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
            self.path = asksaveasfile( defaultextension='*.wsv', filetypes=ftypes, initialfile='workspace1.wsv',
                                       title="Select save directory" )  # show an "Open" dialog box and return the path to the selected file
        if self.path:
            PTApp = gui_logging.var_logging( self.__modules )

            with open( self.path, 'wb' ) as handle:
                pickle.dump( PTApp, handle, protocol=pickle.HIGHEST_PROTOCOL )

    def savework(self):
        """
        save workspace directly is save as has been activated before
        """
        if self.path:
            PTApp = gui_logging.var_logging( self.__modules )

            with open( self.path, 'wb' ) as handle:
                pickle.dump( PTApp, handle, protocol=pickle.HIGHEST_PROTOCOL )

    def loadwork(self):
        MsgBox = 'yes'
        if len( self.frame_map.aoi ) > 0 and self.frame_map.aoi[-1].type != 'Initiate':
            MsgBox = messagebox.askquestion( 'Load Save File',
                                             'Loading saves will clear your AOIs, are you sure?',
                                             icon='warning' )
        if MsgBox == 'yes':
            tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
            save = askopenfilename( title="Load save", filetypes=(("save", "*.wsv"), (
                "all files", "*.*")) )  # show an "Open" dialog box and return the path to the selected file
            with open( save, 'rb' ) as handle:
                PTApp = pickle.load( handle )
            for module in self.__modules:
                for key, value in PTApp[module.name].items():
                    setattr( module, key, value )
            # self.frame_map.canvas.scan_dragto(self.frame_map.centerX, self.frame_map.centerY)
            self.frame_map.reload( mousex=self.frame_map.centerX, mousey=self.frame_map.centerY )
            self.frame_map.web_list_handler( load=True )
            self.route.update_list( self.frame_map.saves )
            self.route.read_csv( None )

    def gmb_archive(self):
        import td_fetch_gmb
        tkinter.Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        save = askdirectory(
            title="Select save directory" )  # show an "Open" dialog box and return the path to the selected file
        if save != '':
            self.progress.config( maximum=4000 + 1, value=1 )
            td_fetch_gmb.fetch_archive( save, self )
        self.headway._archive = save
        directory = os.path.expanduser( '~/Documents/Python_Scripts/WARS/cfg' )
        if not os.path.exists( directory ):
            os.makedirs( directory )
        savename = os.path.join( directory, 'archive.cfg' )
        with open( savename, 'wb' ) as handle:
            pickle.dump( save, handle, protocol=pickle.HIGHEST_PROTOCOL )
        self.destroy()

    def import_routes(self):
        self.headway.clear()
        self.route.read_route()

    def handle_tab_changed(self, event):
        selection = event.widget.select()
        tab = event.widget.tab( selection, "text" )
        if tab == 'log':
            self.log.log_insert()

    def cprint(self, message):
        self.status['text'] = message

    def __init__(self, parent):
        tkinter.Toplevel.__init__( self, parent )
        self.name = 'Mainwindow'
        self.width = 640
        self.height = 640

        self.title( "PT" )
        self.minsize( self.width + 170, self.height + 100 )
        # self.window.maxsize(self.width + 200, self.height + 100)

        self.path = None

        self.filemenu = tkinter.Menu()
        self.config( menu=self.filemenu )
        self.menu1 = tkinter.Menu( self.filemenu, tearoff=0 )
        self.menu1.add_command( label='Save As', command=lambda: self.save_as_work( True ) )
        self.menu1.add_command( label='Save', command=lambda: self.save_as_work( False ) )
        self.menu1.add_command( label='Load', command=self.loadwork )
        self.filemenu.add_cascade( label='File', menu=self.menu1 )

        self.menu2 = tkinter.Menu( self.filemenu, tearoff=0 )
        self.menu2.add_command( label='Create GMB Archive', command=self.gmb_archive )
        self.menu2.add_command( label='Import Routes', command=self.import_routes )
        self.filemenu.add_cascade( label='Import', menu=self.menu2 )

        self.tab_parent = ttk.Notebook( self, width=self.width, height=self.height )

        self.frame_map = gui_frame_canvas.frame_canvas( self, self.tab_parent )
        self.route = displayroutes( self, self.tab_parent )
        self.headway = get_headway( self, self.tab_parent )

        self.__modules = [self, self.frame_map, self.route, self.headway]
        self.log = gui_logging.ShowLog( self, self.tab_parent )
        # self.frame_map.pack()

        self.tab_parent.add( self.log, text="log" )
        self.tab_parent.add( self.frame_map, text="Map" )
        self.tab_parent.add( self.route, text="Route" )
        self.tab_parent.add( self.headway, text="Headway" )

        self.tab_parent.select( 1 )
        self.tab_parent.pack( expand=True, fill=tkinter.BOTH )
        self.tab_parent.bind( "<<NotebookTabChanged>>", self.handle_tab_changed )

        style = ttk.Style()
        style.theme_create( 'Cloud', settings={
            ".": {
                "configure": {
                    "background": '#75b8c8',  # All colors except for active tab-button
                }
            },
            "TNotebook": {
                "configure": {
                    "background": '#0a588f',  # color behind the notebook
                    # [left margin, upper margin, right margin, margin beetwen tab and frames]
                }
            },
            "TNotebook.Tab": {
                "configure": {
                    "background": '#fcf6b1',  # Color of non selected tab-button
                    "padding": [2, 1],
                    # [space beetwen text and horizontal tab-button border, space between text and vertical tab_button border]
                },
                "map": {
                    "background": [("selected", '#aeb0ce')],  # Color of active tab

                }
            }
        } )
        style.theme_use( 'Cloud' )
        style.configure( "red.Horizontal.TProgressbar", troughcolor='azure', background='#98FF98' )

        bottombar = tkinter.Frame( self, height=5 )
        bottombar.pack( expand=False, fill=tkinter.X )
        self.progress = ttk.Progressbar( bottombar, style="red.Horizontal.TProgressbar", orient=tkinter.HORIZONTAL,
                                         length=300, mode='determinate' )
        self.progress.pack( side='right' )

        self.status = tkinter.Label( bottombar, text='Awaiting Area of Interest', bg='white' )

        self.status.pack( side='left' )

        self.frame_map.reload()


if __name__ == "__main__":
    root = tkinter.Tk()
    root.withdraw()
    MainWindow( root )
    root.mainloop()

# for pyinstaller: https://github.com/pyinstaller/pyinstaller/issues/2137  ## install develop
