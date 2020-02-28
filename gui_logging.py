import pickle
import tkinter
import codecs
import pickletools


def var_logging(modules):
    # modules = [self, self.frame_map, self.route, self.headway]
    log = {}
    for module in modules:
        data = {}
        for key, value in module.__dict__.items():
            if not (key.startswith( '_' ) or callable( key ) or not isinstance( value, (
                    str, list, int, float, dict) ) or key in ['children']):
                try:
                    data.update( {key: value} )
                except TypeError:
                    pass
        log[module.name] = data
    return log


class ShowLog( tkinter.Frame ):
    def __init__(self, MainWindow, notebook):
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50,
                                bg='white' )

        frm_a = tkinter.Frame( self, width=self.winfo_reqwidth(), height=self.winfo_reqheight() )
        frm_a.pack()

        log_box = tkinter.Text( frm_a, width=self.winfo_reqwidth(), height=self.winfo_reqheight() )
        log_box.pack()
        log = pickle.dumps( var_logging( MainWindow._MainWindow__modules ), 0 )  # .decode('utf-8')
        pickletools.dis( log )  # , out= 'log.txt')
        log_box.insert( tkinter.INSERT, log )
