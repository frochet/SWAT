import pdb
import argparse
import sqlite3 as lite
import sys
import os
import io
import base64
from PIL import Image
import numpy as np
from datetime import datetime

## canvas version: 0 (150x300)

parser = argparse.ArgumentParser(description="Resize canvas to new dimension")
parser.add_argument("--db", help="path to the sqlite db file", required=True)
parser.add_argument("--newheight", type=int, help="number of rows", required=True)
parser.add_argument("--newwidth", type=int, help="number of columns", required=True)
parser.add_argument("--topleftcoord", help="top left coordinate of the new image (e.g: (4,30) (width, height)", required=True)
parser.add_argument("--pcanvasversion", type=int, help="previous canvas version", required=True)
parser.add_argument("--useremail", help="if provided, we only convert canvas for this user")
parser.add_argument("--removeold", action='store_true')
parser.add_argument("--newversion", type=int, required=True)
def add_to_database(img, user_id, computer_id, newversion, c):
    # convert back to base64

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue())
    img_str = "data:image/png;base64," + img_str
    time = datetime.now().strftime("%B %d, %Y %I:%M%p")
    c.execute("INSERT INTO authc_canvas (computer_id_id, canvas, date_creation, version, feature_nbr_pixels_text)\
            VALUES (:c_id, :canvas, :time, :version, -1)", 
            {"c_id":computer_id, "canvas":img_str, "version":newversion, "time":time})
def canvas_to_numpy_array(canvas, height, width):
    # split function is actually performed to get to image data without the
    # encoding type detail
    img = Image.open(io.BytesIO(base64.b64decode(canvas.split(',')[1])))
    # turns the image into a list of pixels starting at the top left corner
    # line by line
    img_list = list(img.getdata())
    img_nparray = np.array(img_list)
    img_nparray = img_nparray.reshape(height, width, 4) # 4 channels (rgba)
    return img_nparray

def build_dic(canvas, version, c):
    devices_version = {}
    for elem in canvas:
        if elem[1] not in devices_version:
            c.execute("SELECT COUNT(*) FROM authc_canvas WHERE\
                       computer_id_id=:c_id AND version=:version",
                       {"c_id": elem[1], "version": version})
            count = c.fetchone()
            devices_version[elem[1]] = count[0] > 0
    return devices_version
def convert_canvas(args, c):
    if args.pcanvasversion == 0:
        width = 300
        height = 150
    else:
        raise ValueError("No canvas version {0} available".format(args.pcanvasversion))
    top_col = int(args.topleftcoord.split(',')[0].split('(')[1])
    top_row = int(args.topleftcoord.split(',')[1].split(')')[0])

    if args.useremail:
        request = "SELECT auth_user.id, authc_computer.id, authc_canvas.canvas, authc_canvas.version FROM auth_user\
                   INNER JOIN authc_computer\
                   ON auth_user.id = authc_computer.user_id_id\
                   INNER JOIN authc_canvas\
                   ON authc_computer.id = authc_canvas.computer_id_id\
                   WHERE email=:email AND version=0"
    else:
        request = "SELECT auth_user.id, authc_computer.id, authc_canvas.canvas, authc_canvas.version FROM auth_user\
                   INNER JOIN authc_computer\
                   ON auth_user.id = authc_computer.user_id_id\
                   INNER JOIN authc_canvas\
                   ON authc_computer.id = authc_canvas.computer_id_id\
                   WHERE version=0"

    c.execute(request, {"email":args.useremail}) if args.useremail else c.execute(request)
    canvas = c.fetchall()
    devices_version = build_dic(canvas, args.newversion, c)
    #Well... Image has a crop function -_-'
    i = 0
    for elem in canvas:
        if devices_version[elem[1]]:
            continue
        img_array = canvas_to_numpy_array(elem[2], height, width)
        #Checking size
        if top_row + args.newheight > len(img_array):
            print "Dimension mismatch, newheight too large - setting maxheight"
            new_height = len(img_array)-top_row
        else:
            new_height = args.newheight
        if top_col + args.newwidth > len(img_array[0]):
            print "Dimension mismatch, newwidth too large - setting maxwidth"
            new_width = len(img_array[0])-top_col
        else:
            new_width = args.newwidth
        # cropping :)
        newimg_array = img_array[top_row:top_row+new_height, top_col:top_col+new_width]
        img = Image.fromarray(newimg_array.astype('uint8'))
        add_to_database(img, elem[0], elem[1], args.newversion, c)
        if i % 2000 == 0:
            print("Added {0} canvas, {1}% complete".format(i, float(i)/len(canvas)))
        i+=1
        if args.removeold:
            pass 

def canvas_exist(email, version, c):

    if email:
        request = "SELECT COUNT(*) FROM auth_user\
                   INNER JOIN authc_computer\
                   ON authc_computer.user_id_id = auth_user.id\
                   INNER JOIN authc_canvas\
                   ON authc_canvas.computer_id_id = authc_computer.id\
                   WHERE version = :version AND email=:email"
    else:
        return False
    c.execute(request,{"email":email, "version":version})
    count = c.fetchone()
    return count[0] > 0

if __name__ == "__main__":

    args = parser.parse_args()
    connection = lite.connect(args.db)
    c = connection.cursor()
    if canvas_exist(args.useremail, args.newversion, c):
        print "Those canvas are already in the database"
        sys.exit(0)
    convert_canvas(args, c)
    print "commiting the changes..."
    connection.commit()
    print "done."
    c.close()



