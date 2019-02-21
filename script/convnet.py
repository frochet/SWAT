import sqlite3 as lite
import sys
import json
import io
import base64
from PIL import Image
import numpy as np
import pandas as pd
import math
from random import randint
from itertools import cycle
import random
import matplotlib
from matplotlib.colors import ListedColormap
import os
import argparse
from keras.layers.core import Flatten
from keras.callbacks import History 
from keras.layers import Input, Dense, Conv2D, MaxPooling2D, UpSampling2D, Dropout
from keras.models import Model
from keras.callbacks import EarlyStopping
from keras.utils import np_utils
from keras.models import Sequential
from sklearn.metrics import confusion_matrix
import pickle
import pdb

parser = argparse.ArgumentParser(description="Apply a traning phase for a particular user providing the user email and save the trained convnet")
required = parser.add_argument_group("Required arguments")
required.add_argument("--db", help="path to the sqlite db file", required=True)
required.add_argument("--email", help="Training on data from the user having the email provided", required=True)
parser.add_argument("--version", type=int, help="Consider canvas with version number only", default=1)
parser.add_argument("--rcanvas", type=int, help="number of random canvas during learning such that (2000+rcanvas)*(1-val_frac) is a multiple of the batch size (default batch=256)", default=2551)
parser.add_argument("--max_epoch", type=int, default=50)
parser.add_argument("--val_frac", type=float, default=0.1, help="Takes [0, 1] fraction of your training set to evalute on it instead of training on it")
parser.add_argument("--evaluatefp", action="store_true", help="Evaluate 1-Fp in validation set (the validation set contains only no-canvas")
parser.add_argument("--plot", action="store_true", help="plot and save acc, val_acc")
parser.add_argument("--store", action="store_true", help="Save the model computed")
parser.add_argument("--filepath_model", default="models", type=str)
parser.add_argument("--filepath_hist", default="history", type=str)
parser.add_argument("--advanced_arch", action="store_true", help="Use a more complex Sequential CNN")
parser.add_argument("--compid", type=int)

def canvas_to_numpy_array(canvas, height, width):
    """
        Canvas should be the base64 reprensentation of the image strating by image type
        height and width are the size of the image in pixels
    """
    # split function is actually performed to get to image data without the
    # encoding type detail
    img = Image.open(io.BytesIO(base64.b64decode(canvas.split(',')[1])))
    # turns the image into a list of pixels starting at the top left corner
    # line by line
    img_list = list(img.getdata())
    img_nparray = np.array(img_list)/255.0
    img_nparray = img_nparray.reshape(height, width, 4) # 4 channels (rgba)
    return img_nparray


def get_computer_ids(email, c):
    """
    Get a list of computer id associated to this user
    """
    c.execute("SELECT authc_computer.id FROM authc_computer\
               INNER JOIN auth_user\
               ON auth_user.id = authc_computer.user_id_id\
               WHERE email=:email", {"email": email})
    results = c.fetchall()
    return [compid for (compid,) in results]

def get_user_canvas(computerid, version, width, height, c):
    """
    
    Get 2000 canvas from user #email
    if this user has multiple devices,
    get the first device.

    """
    # retrieve all canvas of user #email
    
    #TODO improve request to retrieve only one device

    c.execute('SELECT authc_canvas.canvas FROM authc_canvas\
            WHERE authc_canvas.computer_id_id=:computerid AND version=:version', {"computerid":computerid, "version":version})
    # c.execute('SELECT auth_user.id, email FROM auth_user INNER JOIN authc_computer ON auth_user.id = authc_computer.user_id_id')
    results = c.fetchall()
    if len(results) < 2000:
        sys.exit(-1)
        #raise ValueError("We should have 2000 canvas for user {0} but we have {1}".format(email, len(canvas)))
    return [canvas_to_numpy_array(canvas, height, width) for (canvas,) in results][0:2000]

def get_random_canvas(nbr, email, version, width, height, c):
    """

    get nbr random canvas from different users except user #email

    """
    # Should get the total number of devices from users != email
    c.execute('SELECT authc_computer.id FROM auth_user\
               INNER JOIN authc_computer\
               ON auth_user.id = authc_computer.user_id_id\
               WHERE NOT email=:email', {"email":email})
    computerids = c.fetchall()
    canvas_per_device = nbr/len(computerids) + 1 #handle 0
    results = []
    for (computerid,) in computerids:
        c.execute('SELECT authc_canvas.canvas FROM authc_canvas\
                   WHERE authc_canvas.computer_id_id=:id AND version=:version', {"id":computerid, "version":version})
        tmp_results = c.fetchall()
        #If we have uncomplete set of canvas
        if len(tmp_results) < canvas_per_device:
            continue
        for i in range(0, canvas_per_device):
            elem = random.choice(tmp_results)
            tmp_results.remove(elem)
            results.append(canvas_to_numpy_array(elem[0], height, width))
    return results[0:nbr-1]

def unison_shuffled_copies(a, b):
    """
        Shuffle arrays a and b with the same index permutation
    """
    assert len(a) == len(b)
    p = np.random.permutation(len(a))
    return a[p], b[p]

def train(learning_set, labels, width, height, epoch, val_frac, store,
        advanced, filepath, filepath_hist):
    """!
        Train and validate over a subset of the training set defined by val_frac.
        The subset is not used during training.
    """
    model = Sequential()
    if advanced:
        print "using advanced arch"
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last", input_shape=(height, width, 4)))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        #model.add(MaxPooling2D((2,2), padding='same'))
        model.add(Flatten())
        model.add(Dense(256, activation='relu', kernel_initializer='glorot_normal'))
        #model.add(Dense(128, activation='relu', kernel_initializer='glorot_normal'))
        model.add(Dense(1, activation='sigmoid'))
    else:
        print "Using not advanced arch"
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last", input_shape=(height, width, 4)))
        model.add(MaxPooling2D((3,3), padding='valid'))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), filters=4, padding='valid', data_format="channels_last"))
        model.add(MaxPooling2D((3,3), padding='valid'))
        model.add(Conv2D(activation='relu', kernel_size=(3,3), strides=2, filters=4, padding='valid', data_format="channels_last"))
        model.add(MaxPooling2D((5,5), padding='same'))
        model.add(Flatten())
        model.add(Dense(256, activation='relu', kernel_initializer='glorot_normal'))
        model.add(Dense(1, activation='sigmoid'))

    model.compile(optimizer='adamax', loss='binary_crossentropy', metrics=['accuracy'])
    print "Model compiled"
    if not os.path.exists("test"):
        os.makedirs("test")
    hist = model.fit(learning_set, labels, epochs=epoch, batch_size=256, shuffle=True, verbose=1,
        callbacks = [EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=0, mode='auto')], validation_split=val_frac)
    if store and hist.history['val_acc'][-1] > 0.65: #threshold
        model.save(filepath)
        with open(filepath_hist, 'wb') as histfile:
            pickle.dump(hist.history, histfile)
    return hist



def plot_train_phase(hist):
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
    fig = plt.figure()
    plt.plot(hist.history['acc'])
    plt.plot(hist.history['val_acc'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    fig.savefig("test/test.png")

if __name__ == "__main__":
    

    args = parser.parse_args()
    #test
    connection = lite.connect(args.db)
    c = connection.cursor()
    if args.version == 0:
        width = 300
        height= 150
    elif args.version == 1:
        width = 280
        height = 35
    else:
        print "version not supported"
        sys.exit(-1)
    if args.compid:
        computerids = [args.compid]
    else:
        computerids = get_computer_ids(args.email, c)

    for computerid in computerids:
        print "Getting user canvas... for {0}, computer id {1}".format(args.email, computerid)
        try:
            canvas = get_user_canvas(computerid, args.version, width, height, c)
        except ValueError:
            ## maybe just remove this compid if it happens
            print "REMOVE {0} {1}".format(email, computerid)
            sys.exit(-1)
        print "Got {0} canvas".format(len(canvas))
        print "Getting random canvas..."
        r_canvas = get_random_canvas(args.rcanvas, args.email, args.version, width, height, c)
        print "Got {0} canvas".format(len(r_canvas))
        print "Generate learning set..."
        learning_set = np.concatenate((canvas, r_canvas), axis=0)
        label_yes = [[1]]*len(canvas)
        label_no = [[0]]*len(r_canvas)
        labels = np.concatenate((label_yes, label_no), axis=0)
        if not args.evaluatefp:
            print "Shuffling learning set.."
            learning_set, labels = unison_shuffled_copies(learning_set, labels)
        filepath = args.filepath_model+"/{0}compid{1}.h5".format(args.email.replace("@", "").replace(".", ""), computerid)
        filepath_hist = args.filepath_hist+"/{0}compid{1}.hist".format(args.email.replace("@", "").replace(".", ""), computerid)
        hist = train(learning_set, labels, width, height, args.max_epoch, args.val_frac,
            args.store, args.advanced_arch, filepath, filepath_hist)
        c.execute("UPDATE authc_computer\
                   SET learned_val=:learned_val\
                   WHERE authc_computer.id=:compid",
                  {'learned_val':hist.history['val_acc'][-1], 'compid': computerid})
        connection.commit()
    if args.plot:
        plot_train_phase(hist)
    c.close()
    connection.close()
    sys.exit(0)

