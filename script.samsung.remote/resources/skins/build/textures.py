
import io
import os
import re
import shutil

from Tkinter import Tk
from tkFileDialog import askdirectory

root = Tk()
# Withdraw this widget from the screen such that it is unmapped and forgotten by the window manager. Re-draw it with wm_deiconify.
root.withdraw()

def browse_dir():
    folder = askdirectory(parent=root, initialdir="/", title='Please select a folder of skin source')
    if not bool(folder):
        exit(0)
    #print "You chose %r" % folder
    if not os.path.exists(folder + "/media"):
        raise Error("Subfolder '{}/media' not exist!".format(folder))
    return folder

prefix = "mouse-"
skin_sources_dir = browse_dir() #.replace("\\", "/").strip("/")
# media source
media_sources = skin_sources_dir + "/media"
# backgrounds source
backgrounds = skin_sources_dir + "/backgrounds"
# media destination
media_dst = "../media/"
# backgrounds destination (optional)
bg_dst = media_dst + "backgrounds/"

# get xml's content
list_xml = []
for root, dirs, files in os.walk("../Default/720p"):
    for file in files:
        if file.endswith(".xml"):
            f =  os.path.join(root, file) 
            list_xml.append((open(f).read(), f, False))
print len(list_xml)

for root, dirs, files in os.walk(media_sources): #, topdown=False):
    for file in files:
        fpath = os.path.join(root, file)
        img = fpath.replace(media_sources, "").replace("\\", "/").strip("/")
        for i, str_xml in enumerate(list_xml):
            str_xml, f, changed = str_xml
            dst = media_dst + prefix + img
            if re.search("("+img+")", str_xml) and not re.search("(../"+dst+")", str_xml):
                print dst
                list_xml[i] = (re.sub("("+img+")", "../"+dst, str_xml), f, True)
                if not os.path.exists(os.path.dirname(dst)):
                    os.makedirs(os.path.dirname(dst))
                shutil.copy(fpath, dst)
print

if os.path.exists(backgrounds):
    for root, dirs, files in os.walk(backgrounds):
        for file in files:
            fpath = os.path.join(root, file)
            img = fpath.replace(backgrounds, "").replace("\\", "/").strip("/")
            for i, str_xml in enumerate(list_xml):
                str_xml, f, changed = str_xml
                dst = bg_dst + prefix + img
                if re.search("("+img+")", str_xml) and not re.search("(../"+dst+")", str_xml):
                    print dst
                    list_xml[i] = (re.sub("("+img+")", "../"+dst, str_xml), f, True)
                    if not os.path.exists(os.path.dirname(dst)):
                        os.makedirs(os.path.dirname(dst))
                    shutil.copy(fpath, dst)
print

for str_xml, fxml, changed in list_xml:
    if changed:
        #fxml += ".test.xml"
        with io.open(fxml, 'w+b') as f:
            f.write(str_xml)
        # print fxml
        # print str_xml
        # print
