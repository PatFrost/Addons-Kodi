# -*- coding: utf-8 -*-

import io
import os
import xml.etree.ElementTree as ET


DEFAULT_XML = "script-mouse-test.xml"


def save(res, tostring):
    fxml = "../Default.{}/{}/{}".format(res, res, DEFAULT_XML)
    if not os.path.exists(os.path.dirname(fxml)):
        os.makedirs(os.path.dirname(fxml))

    if os.path.exists(fxml):
        os.remove(fxml)

    with io.open(fxml, 'w+b') as f:
        f.write(u'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(unicode(tostring, "utf-8"))

    # with open(fxml, 'wb') as f:
        # f.write(u'<?xml version="1.0" encoding="UTF-8"?>\n')
        # f.write(unicode(tostring, "utf-8"))
        #f.write(u"\n<!-- ° -->")

def getScaling(num, scale):
    try: newnum = str(int(num.strip("r"))*scale)
    except: newnum = str(float(num.strip("r"))*scale)
    if newnum.endswith(".0"):
        newnum = newnum.split(".")[0]
    if num.endswith("r"):
        newnum += "r"
    return newnum

def setScaling(res):
    if res == "21x9":
        scalex = 2.0
        scaley = 1.5
    elif res == "1080i":
        scalex = 1.5
        scaley = 1.5
    else:
        scalex = 0.0
        scaley = 0.0

    tree = ET.parse("../Default/720p/"+DEFAULT_XML)
    root = tree.getroot()

    tags = [("left", scalex), ("width",  scalex),
            ("top",  scaley), ("height", scaley),
            ("bordersize", scalex), ("bordertexture", scalex)]
    for tag, scale in tags:
        for elem in root.findall(".//"+tag):
            num = elem.text or "0"
            if num == "auto" or tag == "bordertexture":
                newattrib = {}
                for k, v in elem.attrib.items():
                    newattrib[k] = getScaling(v, scale)
                elem.attrib = newattrib
                print(res, tag, elem.attrib, newattrib)
            else:
                newnum = getScaling(num, scale)
                elem.text = newnum
                print(res, tag, num, newnum)
    # tree.write("../"res+"/"+DEFAULT_XML, encoding='UTF-8', xml_declaration=True)
    save(res, ET.tostring(root))

setScaling("21x9")
setScaling("1080i")
