import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import sys, os
from os import listdir
from os.path import isfile, join
import sqlite3 as lite
import cPickle as pickle
import pdb
from keras.models import load_model
from PIL import Image
import io
import base64
import numpy as np
import argparse 
import pickle
from convnet_plot import canvas_to_numpy_array


parser = argparse.ArgumentParser(description="Plot results from convnet.py")
required =  parser.add_argument_group("Required arguements")
required.add_argument("--basepath", help="path where directorys of models and history are stored")
parser.add_argument("--nbr_canvas_b", type=int, default=10, help="Number of batches of 32 canvas to fetch for each user")
parser.add_argument("--store_devicelist", action="store_true")
parser.add_argument("--load_devicelist", action="store_true")

if __name__ ==  "__main__":

  args = parser.parse_args()
  mypath = args.basepath
  if not args.load_devicelist:
      mypathmodels = mypath+"/models"
      mypathmodelsadv = mypath+"/models_adv"
      allhistfiles = [f for f in listdir(mypath+"/history") if isfile(join(mypath+"/history", f))]
      allmodelfiles = [f for f in listdir(mypathmodels) if isfile(join(mypathmodels, f))]
      allhistfiles_adv = [f for f in listdir(mypath+"/history_adv") if isfile(join(mypath+"/history_adv", f))]
      allmodelfiles_adv = [f for f in listdir(mypathmodelsadv) if isfile(join(mypathmodelsadv, f))]
      
      connection = lite.connect("/home/frochet/C-Cure/canvasauth/db.sqlite3")
      c = connection.cursor()
      version = 1
      c.execute('SELECT auth_user.email, authc_computer.id, authc_computer.os_family, authc_computer.browser_family, authc_computer.is_mobile FROM auth_user,\
                 authc_computer\
                 WHERE\
                 auth_user.id = authc_computer.user_id_id')
      results = c.fetchall()
      devicelist = {}
      for device in results:
        if device[0].replace("@","").replace(".","")+"compid"+str(device[1]) not in devicelist:
          f = device[0].replace("@", "").replace(".", "")+"compid"+str(device[1])+".h5"
          if not isfile(join(mypathmodels, f)):
            continue
          devicelist[device[0].replace("@","").replace(".","")+"compid"+str(device[1])] = list(device)
      print "Getting {0} canvas from the database for each device".format(args.nbr_canvas_b)
      height = 35
      width = 280
      for email in devicelist:
          c.execute('SELECT authc_canvas.canvas FROM authc_canvas, authc_computer\
                     WHERE authc_canvas.computer_id_id=authc_computer.id\
                     AND authc_computer.id=:idcomp AND version=:version\
                     LIMIT :nbr_canvas', {"idcomp":int(devicelist[email][1]), "version":version,
                                          "nbr_canvas":args.nbr_canvas_b*32})
          results = c.fetchall()
          if len(results) == 0:
              print "no canvas result for {0} {1}".format(email, devicelist[email][1])
              del devicelist[email]
          print "Got {0}'s  {1} canvas".format(email, len(results))
          devicelist[email].append([canvas_to_numpy_array(canvas, height, width) for (canvas,) in results])
      connection.close()
      #devicelist[email][5] should contain all canvas

      
      allmodels = {}
      allmodelsadv = {}
      print "Loading models"
      count = 0

      #God this shit is annormaly slow
      for f in allmodelfiles:
        allmodels[f.split('.')[0]] = load_model(mypathmodels+"/"+f, compile=False)
        count+=1
        print "Loaded model {0}/{1}".format(count, len(allmodelfiles)*2)


      for f in allmodelfiles_adv:
        allmodelsadv[f.split('.')[0]] = load_model(mypathmodelsadv+"/"+f, compile=False)
        count+=1
        print "Loaded model {0}/{1}".format(count, len(allmodelfiles)*2)
      
      for email in devicelist:
        devicelist[email].append([{} for i in range(0, args.nbr_canvas_b)]) #[6]
        devicelist[email].append([{} for i in range(0, args.nbr_canvas_b)]) #[7]
        #truep on [8] and [9]
        devicelist[email].append(
                [np.median(allmodels[email].predict(np.array(devicelist[email][5][(i-1)*32:i*32-1]))) for i in range(1, args.nbr_canvas_b+1)]
                ) #8
        devicelist[email].append(
            [np.median(allmodelsadv[email].predict(np.array(devicelist[email][5][(i-1)*32:i*32-1]))) for i in range(1, args.nbr_canvas_b+1)]
                ) #9
        #median glob [10] and [11]
        devicelist[email].append(np.median(allmodels[email].predict(np.array(devicelist[email][5]))))
        devicelist[email].append(np.median(allmodelsadv[email].predict(np.array(devicelist[email][5]))))
      
      for email in devicelist:
        for modelname in devicelist:
          if email != modelname:
            for i in range(1, args.nbr_canvas_b+1):
              predict = np.median(allmodels[modelname].predict(np.array(devicelist[email][5][(i-1)*32:i*32-1])))
              devicelist[email][6][i-1][modelname] = predict
              predict = np.median(allmodelsadv[modelname].predict(np.array(devicelist[email][5][(i-1)*32:i*32-1])))
              devicelist[email][7][i-1][modelname] = predict
        print "Computed predictions for user {0}".format(email)
      print "Computing CDFs and plotting mean"
      if args.store_devicelist:
          with open('devicelist.pickle', "wb") as datafile:
              pickle.dump(devicelist, datafile)
  else:
      print "Loading pickle file..."
      devicelist = pickle.load(open(mypath+"/devicelist.pickle", "rb"))
      print "File loaded."
      

    
  # Now plot roc curves of authentication given an interval value arount [10] or [11]
  interval = np.linspace(0,1, 200)
  true_pos_r = []
  true_pos_r_adv = []
  false_pos_r = []
  false_pos_r_adv = []
  retain_fpos_r = 1
  retain_fpos_r_adv = 1
  retain_inter  = 0
  retain_inter_adv = 0
  for int_val in interval:
    true_pos_r.append(0)
    true_pos_r_adv.append(0)
    false_pos_r.append(0)
    false_pos_r_adv.append(0)
    for email in devicelist:
      for other_user in devicelist:
        if other_user == email:
          #tpr
          for tpr in devicelist[email][8]:
            if tpr >= (devicelist[email][10]-int_val) and tpr <= (devicelist[email][10]+int_val):
              true_pos_r[-1] += 1
          for tpr in devicelist[email][9]:
            if tpr >= (devicelist[email][11]-int_val) and tpr <= (devicelist[email][11]+int_val):
              true_pos_r_adv[-1] += 1
        else:
          for fpr in devicelist[email][6]:
            if fpr[other_user] >= (devicelist[email][10]-int_val) and fpr[other_user] <= (devicelist[email][10]+int_val):
              false_pos_r[-1] += 1
          for fpr in devicelist[email][7]:
            if fpr[other_user] >= (devicelist[email][11]-int_val) and fpr[other_user] <= (devicelist[email][11]+int_val):
              false_pos_r_adv[-1] += 1
    true_pos_r[-1] = float(true_pos_r[-1])/(len(devicelist)*args.nbr_canvas_b)
    true_pos_r_adv[-1] = float(true_pos_r_adv[-1])/(len(devicelist)*args.nbr_canvas_b)
    false_pos_r[-1] = float(false_pos_r[-1])/(args.nbr_canvas_b*len(devicelist)*(len(devicelist)-1))
    false_pos_r_adv[-1] = float(false_pos_r_adv[-1])/(args.nbr_canvas_b*len(devicelist)*(len(devicelist)-1))
    if true_pos_r[-1]  == 1 and retain_fpos_r > false_pos_r[-1]:
      retain_fpos_r = false_pos_r[-1]
      retain_inter = int_val
    if true_pos_r_adv[-1] == 1 and retain_fpos_r_adv > false_pos_r_adv[-1]:
      retain_fpos_r_adv = false_pos_r_adv[-1]
      retain_inter_adv = int_val

  plt.figure()
  plt.xlim(xmax=0.2)
  plt.axvline(x = retain_fpos_r, linestyle="--", color="k")
  plt.axvline(x = retain_fpos_r_adv, linestyle="--", color="k")
  print "best interval size for first arch: 2*{0}".format(retain_inter)
  print "best interval size for second arch: 2*{0}".format(retain_inter_adv)
  plt.xlabel("False Positive Rate")
  plt.ylabel("True Positive Rate")
  arch1, = plt.plot(false_pos_r, true_pos_r, label="Arch 1")
  arch2, = plt.plot(false_pos_r_adv, true_pos_r_adv, label="Arch 2")
  plt.legend(handles=[arch1, arch2])
  plt.savefig('roc_intthresh')
  

