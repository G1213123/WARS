import pickle
import pickletools
import sys
import tkinter
from io import StringIO


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
        try:
            log[module.name] = data
        except AttributeError:
            log['AoiInstance'] = data
    return log


class ShowLog( tkinter.Frame ):
    def __init__(self, MainWindow, notebook):
        tkinter.Frame.__init__( self, notebook, width=MainWindow.width + 100, height=MainWindow.height + 50,
                                bg='white' )

        frm_a = tkinter.Frame( self, width=self.winfo_reqwidth(), height=self.winfo_reqheight() )
        frm_a.pack()

        self.log_box = tkinter.Text( frm_a, width=self.winfo_reqwidth(), height=self.winfo_reqheight() )
        self.log_box.pack()

        self.window = MainWindow

    def log_insert(self):
        log2 = pickle.dumps( var_logging( self.window._MainWindow__modules ), 0 )
        log1 = pickle.dumps( var_logging( self.window.frame_map.aoi ), 0 )

        old_stdout = sys.stdout
        # This variable will store everything that is sent to the standard output
        result = StringIO()
        sys.stdout = result

        pickletools.dis( log2 )
        pickletools.dis( log1 )

        sys.stdout = old_stdout
        result_string = result.getvalue()
        self.log_box.insert( tkinter.INSERT, result_string )
