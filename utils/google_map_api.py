"""
Api key related utilities
Using Google Map Static API service
related url:
https://developers.google.com/maps/documentation/maps-static/get-api-key
"""
import os
import pickle
import tkinter
import webbrowser

DIRECTORY = os.path.expanduser('~/Documents/Python_Scripts/WARS/cfg')
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)


def callback(url):
    webbrowser.open_new(url)


class ApiInput(tkinter.Toplevel):
    def __init__(self, **kw):
        super().__init__()
        self.geometry("%dx%d%+d%+d" % (500, 120, 250, 125))
        self.l1 = tkinter.Label(self, text="Google Map Static Map API key")
        self.l1.pack()
        self.l2 = tkinter.Label(self, text="For details of obtaining a key, see the following link:")
        self.l2.pack()
        self.l3 = tkinter.Label(self, text="https://developers.google.com/maps/documentation/maps-static/get-api-key",
                                fg="blue", cursor="hand2", font="Verdana 8 underline")
        self.l3.pack()
        self.l3.bind("<Button-1>",
                     lambda e: callback("https://developers.google.com/maps/documentation/maps-static/get-api-key"))
        self.f = tkinter.Frame(self)
        self.f.pack()
        self.l4 = tkinter.Label(self.f, text="Insert API key:")
        self.l4.pack(side=tkinter.LEFT)
        self.e = tkinter.Entry(self.f, width=50)
        self.e.pack(side=tkinter.RIGHT)
        self.b = tkinter.Button(self, text='Ok', command=self.cleanup)
        self.b.pack()

        self.name = 'api_setting'
        self.title(self.name)

    def cleanup(self):
        self.value = self.e.get()
        if self.value != "":
            # create save config file directory
            self.savename = DIRECTORY + r'/api.cfg'
            # Create the file if it does not exist
            with open( self.savename, 'wb' ) as handle:
                pickle.dump( self.value, handle, protocol=pickle.HIGHEST_PROTOCOL )
        self.destroy()


def load_api():
    savename = os.path.expanduser('~/Documents/Python_Scripts/WARS/cfg/api.cfg')
    try:
        with open(savename, 'rb') as handle:
            api = pickle.load(handle)
    except (OSError, IOError) as e:
        return None
    return api


if __name__ == "__main__":
    root = tkinter.Tk()
    root.withdraw()

    ApiInput()
    root.mainloop()
