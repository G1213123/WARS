import datetime
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

import pandas as pd


# File path prompt
def file_prompt():
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(title="Select route list", filetypes=(("comma seperated values", "*.csv"), (
        "all files", "*.*")))  # show an "Open" dialog box and return the path to the selected file
    # print(filename)
    return filename


# Save file prompt
def save_prompt():
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    savename = asksaveasfilename(defaultextension=".csv", title="save file",
                                 filetypes=(("comma seperated values", "*.csv"), ("all files", "*.*")))
    # print(filename)
    return savename


# Default file save location
class file_init:
    def __init__(self, savename):
        self.filename = file_prompt()
        if savename is None:
            self.savename = save_prompt()


# get a file prompt for if route argument not provided
def read_route(route, savename):
    if route is None:
        file_path = file_init(savename)
        route = pd.read_csv(file_path.filename, header=None, index_col=False)
    route = file_format(route)
    if savename is None:
        savename = file_path.savename
    return route, savename


def file_format(route):
    # Detect wide or long data format
    try:
        if len(route.index) == 1:
            route = route.iloc[0]
        else:
            route = route.iloc[:, 0]

        # Correct input data
        route = route.astype(str)
        route = [x.upper() for x in route]
        route = [x.strip() for x in route]
        route = list(dict.fromkeys(route))
    except:
        pass
    return route


# Check peak hour
def time_in_period(x, y, start, end):
    """Return true if x is in the range [start, end]"""
    if not isinstance(start, datetime.time):
        start = float_to_time(start)
        end = float_to_time(end)
    if end == datetime.time(0, 0, 0):
        end = datetime.time(23, 59, 59)
    if y < x:
        x1 = x
        y1 = datetime.time(23, 59, 59)
        x2 = datetime.time(0, 0, 0)
        y2 = y
    else:
        x1 = x
        x2 = x
        y1 = y
        y2 = y
    return (start <= x1 < end or start < y1 <= end) or (x1 < start and y1 > end) or \
           (start <= x2 < end or start < y2 <= end) or (x2 < start and y2 > end)


def float_to_time(x):
    time = int(x) * 60
    return datetime.time(divmod(time, 60)[0], divmod(time, 60)[1], 0)


if __name__ == "__main__":
    read_route([])
