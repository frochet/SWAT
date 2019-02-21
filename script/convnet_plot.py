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
import time

parser = argparse.ArgumentParser(description="Plot results from convnet.py")
required =  parser.add_argument_group("Required arguements")
required.add_argument("--basepath", help="path where directorys of models and history are stored")
parser.add_argument("--compare", action="store_true", help="If given, we plot our results from directory"
  " models to compare with results from directory models_adv")
parser.add_argument("--store_pickle", action="store_true", help="If given, we output pickle files"
        " of our distributions")
parser.add_argument("--truep", action="store_true", help="add a boxplot of trupositives")
parser.add_argument("--roc", action="store_true", help="add roc curves")

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


#load historical data of all learned users

def plot_min_max_median(minhist, maxhist, medianhist):
    fig = plt.figure()
    plt.plot(maxhist['acc'], color="purple")
    plt.plot(maxhist['val_acc'], color="purple", linestyle='-.')
    plt.plot(medianhist['acc'], color="green")
    plt.plot(medianhist['val_acc'], color="green", linestyle='-.')
    plt.plot(minhist['acc'], color="blue")
    plt.plot(minhist['val_acc'], color="blue", linestyle='-.')
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['best - train',
                'best - validation',
                'median - train',
                'median - validation',
                'worst - train',
                'worst - validation'])
    fig.savefig('maxmedianminacc.png')

##### Plotting functions #####
# Code cf, getcdf borrowed from pathsim_plot.py written by Aaron Johnson (https://github.com/torps)
## helper - cumulative fraction for y axis
def cf(d): return np.arange(1.0,float(len(d))+1.0)/float(len(d))

## helper - return step-based CDF x and y values
## only show to the 99th percentile by default
def getcdf(data, shownpercentile=0.99):
    data.sort()
    frac = cf(data)
    x, y, lasty = [], [], 0.0
    for i in xrange(int(round(len(data)*shownpercentile))):
        x.append(data[i])
        y.append(lasty)
        x.append(data[i])
        y.append(frac[i])
        lasty = frac[i]
    return (x, y)

def compute_predictions(devicelist, typemode):

  # Now plotting window10 cdf
  tmp_windows10 = {}
  tmp_linux = {}
  tmp_ios = {}
  tmp_macos = {}
  tmp_firefox = {}
  tmp_chrome = {}
  tmp_winchrome = {}
  tmp_winfirefox = {}
  tmp_linuxfirefox = {}
  tmp_linuxchrome = {}
  if typemode == "models":
      index = 6
  else:
      index = 7
  for email in devicelist:
      if devicelist[email][2] == "Windows 10" or devicelist[email][2] == "Windows 7":
          tmp_windows10[email] = []
          for email2 in devicelist:
              if (devicelist[email2][2] == "Windows 10" or devicelist[email2][2] == "Windows 7") and\
                      email != email2:
                  tmp_windows10[email].append(devicelist[email][index][email2])
      if devicelist[email][2] == "Linux" or devicelist[email][2] == "Ubuntu":
          tmp_linux[email] = []
          for email2 in devicelist:
              if (devicelist[email2][2] == "Linux" or devicelist[email2][2] == "Ubuntu") and\
                      email != email2:
                  tmp_linux[email].append(devicelist[email][index][email2])
      if devicelist[email][2] == "Mac OS X":
          tmp_macos[email] = []
          for email2 in devicelist:
              if devicelist[email2][2] == devicelist[email][2] and email2 != email:
                  tmp_macos[email].append(devicelist[email][index][email2])
      if devicelist[email][3] == "Firefox":
          tmp_firefox[email] = []
          for email2 in devicelist:
              if devicelist[email2][3] == devicelist[email][3] and email2 != email:
                  tmp_firefox[email].append(devicelist[email][index][email2])
      if devicelist[email][3] == "Chrome":
          tmp_chrome[email] = []
          for email2 in devicelist:
              if devicelist[email2][3] == devicelist[email][3] and email2 != email:
                  tmp_chrome[email].append(devicelist[email][index][email2])
      if (devicelist[email][2] == "Windows 10" or devicelist [email][2] == "Windows 7") and\
         (devicelist[email][3] == "Firefox"):
          tmp_winfirefox[email] = []
          for email2 in devicelist:
              if (devicelist[email2][2] == "Windows 10" or devicelist[email2][2] == "Windows 7") and\
                      (devicelist[email2][3] == devicelist[email][3]) and email != email2:
                  tmp_winfirefox[email].append(devicelist[email][index][email2])
      if (devicelist[email][2] == "Windows 10" or devicelist [email][2] == "Windows 7") and\
         (devicelist[email][3] == "Chrome"):
          tmp_winchrome[email] = []
          for email2 in devicelist:
              if (devicelist[email2][2] == "Windows 10" or devicelist[email2][2] == "Windows 7") and\
                      (devicelist[email2][3] == devicelist[email][3]) and email != email2:
                  tmp_winchrome[email].append(devicelist[email][index][email2])
      if (devicelist[email][2] == "Linux" or devicelist[email][2] == "Ubuntu") and\
         (devicelist[email][3] == "Firefox"):
         tmp_linuxfirefox[email] = []
         for email2 in devicelist:
              if (devicelist[email2][2] == "Linux" or devicelist[email2][2] == "Ubuntu") and\
                      devicelist[email2][3] == devicelist[email][3] and email != email2:
                  tmp_linuxfirefox[email].append(devicelist[email][index][email2])
      if (devicelist[email][2] == "Linux" or devicelist[email][2] == "Ubuntu") and\
         (devicelist[email][3] == "Chrome"):
         tmp_linuxchrome[email] = []
         for email2 in devicelist:
              if (devicelist[email2][2] == "Linux" or devicelist[email2][2] == "Ubuntu") and\
                      devicelist[email2][3] == devicelist[email][3] and email != email2:
                  tmp_linuxchrome[email].append(devicelist[email][index][email2])
      if (devicelist[email][2] == "iOS"):
          tmp_ios[email] = []
          for email2 in devicelist:
              if devicelist[email2][2] == devicelist[email][2] and email2 != email:
                  tmp_ios[email].append(devicelist[email][index][email2])
  return tmp_windows10, tmp_linux, tmp_macos, tmp_firefox, tmp_chrome, tmp_winchrome, tmp_winfirefox, tmp_linuxfirefox, tmp_linuxchrome, tmp_ios


if __name__ == "__main__":
  
  args = parser.parse_args()

  mypath = args.basepath
  mypathmodels = mypath+"/models"
  if args.compare:
      mypathmodelsadv = mypath+"/models_adv"

  allhistfiles = [f for f in listdir(mypath+"/history") if isfile(join(mypath+"/history", f))]
  allmodelfiles = [f for f in listdir(mypathmodels) if isfile(join(mypathmodels, f))]
  if args.compare:
      allhistfiles_adv = [f for f in listdir(mypath+"/history_adv") if isfile(join(mypath+"/history_adv", f))]
      allmodelfiles_adv = [f for f in listdir(mypathmodelsadv) if isfile(join(mypathmodelsadv, f))]

  # Load all information from the database 
  connection = lite.connect("/home/frochet/C-Cure/canvasauth/db.sqlite3")
  c = connection.cursor()
  version = 1
  #c.execute('SELECT auth_user.email, authc_computer.id, authc_computer.os_family, authc_computer.browser_family, authc_computer.is_mobile FROM auth_user\
  #        INNER JOIN authc_computer\
  #        ON auth_user.id = authc_computer.user_id_id\
  #        INNER JOIN authc_canvas\
  #        ON authc_computer.id = authc_canvas.computer_id_id\
  #        WHERE version=:version', {"version":version})
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
  connection.close()
  #we should have now a list of tupples
  ## Plot min-max-median of all
  allhist = [(f, pickle.load(open(mypath+"/history/"+f, "rb"))) for f in allhistfiles]
  allhist.sort(key=lambda x: x[1]['val_acc'][-1])
  minhist = allhist[0][1]
  maxhist = allhist[-1][1]
  medianhist = allhist[len(allhist)/2][1]

  if args.compare:
      allhistadv = [(f, pickle.load(open(mypath+"/history_adv/"+f, "rb"))) for f in allhistfiles]
      allhistadv.sort(key=lambda x: x[1]['val_acc'][-1])
      minhistadv = allhistadv[0][1]
      maxhistadv = allhistadv[-1][1]
      medianhistadv = allhistadv[len(allhist)/2][1]

  print "Drawing the model accuracy"
  if args.compare:
    plot_min_max_median(minhistadv, maxhistadv, medianhistadv)
  else:
    plot_min_max_median(minhist, maxhist, medianhist)
    
  print "Drawing a pie plot of OS family and Browser family"
  #do pie plot of OS family
  plt.figure()
  tot = len(devicelist)
  osfamily = {}
  brfamily = {}
  for device in devicelist.values():
      if device[2] not in osfamily:
          osfamily[device[2]] = 1
      else:
          osfamily[device[2]]+=1
      if device[3] not in brfamily:
          brfamily[device[3]] = 1
      else:
          brfamily[device[3]] +=1
      
  plt.axis('equal')
  plt.pie(osfamily.values(), labels=osfamily.keys())
  plt.savefig('piechartos.png')
  plt.figure()
  plt.pie(brfamily.values(), labels = brfamily.keys(), labeldistance=1.3)
  plt.axis('equal')
  plt.savefig('piechartbrowser.png')
  #do same plot but with bars instead
  fig, ax1 = plt.subplots()
  pos = np.arange(len(osfamily))
  sorted_osfamily = sorted(osfamily.iteritems(), key= lambda (k,v): (v,k))
  rects = ax1.barh(pos, [(float(elem)/len(devicelist))*100 for key, elem in sorted_osfamily],
          align='center',
          height=0.5,
          color='blue',
          tick_label=[key for key, elem in sorted_osfamily])
  ax1.set_xlabel("Percentage %")
  plt.tight_layout()
  plt.show()
  plt.savefig('barchartos.png')
    
  fig, ax1 = plt.subplots()
  pos = np.arange(len(brfamily))
  sorted_brfamily = sorted(brfamily.iteritems(), key=lambda (k, v): (v,k))
  rects = ax1.barh(pos, [(float(elem)/len(devicelist))*100 for key, elem in sorted_brfamily],
                    align='center',
                    height=0.5,
                    color='blue',
                    tick_label=[key for key, elem in sorted_brfamily])
  ax1.set_xlabel("Percentage %")
  plt.tight_layout()
  plt.show()
  plt.savefig('barchartbrowser.png')

  sys.exit(0)

  print "Getting 32 canvas from the database for each device"
  connection = lite.connect("/home/frochet/C-Cure/canvasauth/db.sqlite3")
  c = connection.cursor()
  height = 35
  width = 280
  for email in devicelist:
      c.execute('SELECT authc_canvas.canvas FROM authc_canvas, authc_computer\
                 WHERE authc_canvas.computer_id_id=authc_computer.id\
                 AND authc_computer.id=:idcomp AND version=:version\
                 LIMIT 32', {"idcomp":int(devicelist[email][1]), "version":version})
      results = c.fetchall()
      if len(results) == 0:
          print "no canvas result for {0} {1}".format(email, devicelist[email][1])
          del devicelist[email]
      print "Got {0}'s  {1} canvas".format(email, len(results))
      devicelist[email].append([canvas_to_numpy_array(canvas, height, width) for (canvas,) in results])
  connection.close()
  #devicelist[email][5] should contain all canvas
  print "Now computing CDF of predictions"
  allmodels = {}

  for f in allmodelfiles:
    allmodels[f.split('.')[0]] = load_model(mypathmodels+"/"+f, compile=False)
  if args.compare:
    allmodelsadv = {}
    for f in allmodelfiles_adv:
      allmodelsadv[f.split('.')[0]] = load_model(mypathmodelsadv+"/"+f, compile=False)

  print "Loaded all models"
  bad_model = {}
  bad_model_adv = {}
  for email in devicelist:
      devicelist[email].append({}) #[6]
      if args.compare:
        devicelist[email].append({}) #[7]
      if args.truep:
        devicelist[email].append(np.median(allmodels[email].predict(np.array(devicelist[email][5])))) #8
        ## Fix - remove abnormal data. Investigate !
        if devicelist[email][8] < 0.5:
            bad_model[email] = email
            print "bad model: {0}".format(email)
        if args.compare:
            devicelist[email].append(np.median(allmodelsadv[email].predict(np.array(devicelist[email][5])))) #9
            if devicelist[email][9] < 0.5:
                bad_model_adv[email] = email
                print "bad model adv: {0}".format(email)
  
  for email in bad_model:
      if args.compare and email in bad_model_adv:
          del devicelist[email]
      elif not args.compare:
          del devicelist[email]

  for email in devicelist:
      for modelname in devicelist.keys():
          if email != modelname:
              if email not in bad_model and modelname not in bad_model:
                  predict = np.median(allmodels[modelname].predict(np.array(devicelist[email][5])))
                  devicelist[email][6][modelname] = predict
              if args.compare:
                  if email not in bad_model_adv and modelname not in bad_model_adv:
                      predict = np.median(allmodelsadv[modelname].predict(np.array(devicelist[email][5])))
                      if (predict >= 0.85):
                          print "{0} predicted {1} for user {2} for the advanced arch".format(modelname, predict, email)
                      devicelist[email][7][modelname] = predict
      print "Computed {0} predictions for user {1}".format(len(devicelist[email][6]), email)
  print "Computing CDFs and plotting mean"
    
  if args.store_pickle:
      with open('data.pickle', "wb") as datafile:
          pickle.dump(devicelist, datafile)

  all_users_predictions = []
  for email in devicelist:
      all_users_predictions.extend(devicelist[email][6].values())
  x, y = getcdf(all_users_predictions)
  plt.figure()
  plt.plot(x,y, color="purple")
  if args.compare:
    all_users_predictions = []
    for email in devicelist:
      all_users_predictions.extend(devicelist[email][7].values())
    x, y = getcdf(all_users_predictions)
    plt.plot(x, y, color="purple", linestyle="-.")
  
  
  tmp_windows10, tmp_linux, tmp_macos, tmp_firefox, tmp_chrome, tmp_winchrome, tmp_winfirefox, tmp_linuxfirefox, tmp_linuxchrome, tmp_ios = compute_predictions(devicelist, "models")
  tmp_windows10_adv, tmp_linux_adv, tmp_macos_adv, tmp_firefox_adv, tmp_chrome_adv, tmp_winchrome_adv, tmp_winfirefox_adv, tmp_linuxfirefox_adv, tmp_linuxchrome_adv, tmp_ios_adv = compute_predictions(devicelist, "models_adv")

  windows_predictions = []
  linux_predictions   = []
  macos_predictions   = []
  ios_predictions     = []
  for email in tmp_windows10:
      windows_predictions.extend(tmp_windows10[email])
  x, y = getcdf(windows_predictions)
  plt.plot(x,y, color="blue")
  if args.compare:
      windows_predictions = []
      for email in tmp_windows10_adv:
          windows_predictions.extend(tmp_windows10_adv[email])
      x, y = getcdf(windows_predictions)
      plt.plot(x,y, color="blue", linestyle="-.")

  for email in tmp_linux:
      linux_predictions.extend(tmp_linux[email])
  x, y = getcdf(linux_predictions)
  plt.plot(x,y, color="red")
  if args.compare:
      linux_predictions = []
      for email in tmp_linux_adv:
          linux_predictions.extend(tmp_linux_adv[email])
      x, y = getcdf(linux_predictions)
      plt.plot(x,y, color="red", linestyle="-.")

  for email in tmp_macos:
      macos_predictions.extend(tmp_macos[email])
  x, y = getcdf(macos_predictions)
  plt.plot(x,y, color="green")
  if args.compare:
      macos_predictions = []
      for email in tmp_macos_adv:
          macos_predictions.extend(tmp_macos_adv[email])
      x, y = getcdf(macos_predictions)
      plt.plot(x,y, color="green", linestyle="-.")
  for email in tmp_ios:
      ios_predictions.extend(tmp_ios[email])
  x, y = getcdf(ios_predictions)
  plt.plot(x, y, color="black")
  if args.compare:
      ios_predictions = []
      for email in tmp_ios_adv:
          ios_predictions.extend(tmp_ios_adv[email])
      x, y = getcdf(ios_predictions)
      plt.plot(x, y, color="black", linestyle="-.")
  plt.title('CDFs of predictions of each OS over the others of the same family')
  plt.ylabel('CDF')
  plt.xlabel('Prediction over other users\' learned model')
  if args.compare:
      plt.legend(['all', 'all adv', 'Windows', 'Windows adv', 'Linux', 'Linux adv',\
              'Mac OS X', 'Mac OS X adv', 'iOS', 'iOS adv'], loc='lower right')
  else: 
      plt.legend(['all','Windows', "Linux", "Mac OS X", "iOS"])
  plt.savefig('cdfalluserspredictions')

  firefox_predictions = []
  chrome_predictions = []
  x, y = getcdf(all_users_predictions)
  plt.figure()
  if args.compare:
      plt.plot(x,y, color="orange", linestyle="-.")
  else:
      plt.plot(x,y)
  if args.compare:
      all_users_predictions = []
      for email in devicelist:
          all_users_predictions.extend(devicelist[email][6].values())
      x, y = getcdf(all_users_predictions)
      plt.plot(x,y, color="orange")

  for email in tmp_firefox:
      firefox_predictions.extend(tmp_firefox[email])
  x,y = getcdf(firefox_predictions)
  plt.plot(x,y, color="black")
  if args.compare:
      firefox_predictions = []
      for email in tmp_firefox_adv:
          firefox_predictions.extend(tmp_firefox_adv[email])
      x, y = getcdf(firefox_predictions)
      plt.plot(x, y, color="black", linestyle="-.")
  for email in tmp_chrome:
      chrome_predictions.extend(tmp_chrome[email])
  x, y = getcdf(chrome_predictions)
  plt.plot(x, y, color="blue")
  if args.compare:
      chrome_predictions = []
      for email in tmp_chrome_adv:
          chrome_predictions.extend(tmp_chrome_adv[email])
      x, y = getcdf(chrome_predictions)
      plt.plot(x, y, color="blue", linestyle="-.")

  plt.title('CDFs of predictions of each Browser over the others of the same family')
  plt.ylabel('CDF')
  plt.xlabel('Prediction over other users\' learned model')
  plt.legend(['all adv', 'all', 'Firefox','Firefox adv', 'Chrome', 'Chrome adv'])
  plt.savefig('cdfallbrowserspredictions')
  winfirefox_predictions = []
  winchrome_predictions = []
  linuxfirefox_predictions = []
  linuxchrome_predictions = []
  plt.figure()
  for email in tmp_winfirefox:
      winfirefox_predictions.extend(tmp_winfirefox[email])
  x, y = getcdf(winfirefox_predictions)
  plt.plot(x,y)
  for email in tmp_winchrome:
      winchrome_predictions.extend(tmp_winchrome[email])
  x, y = getcdf(winchrome_predictions)
  plt.plot(x,y)
  for email in tmp_linuxfirefox:
      linuxfirefox_predictions.extend(tmp_linuxfirefox[email])
  x, y = getcdf(linuxfirefox_predictions)
  plt.plot(x,y)
  for email in tmp_linuxchrome:
      linuxchrome_predictions.extend(tmp_linuxchrome[email])
  x, y = getcdf(linuxchrome_predictions)
  plt.plot(x,y)
  plt.title('CDFs of prediction of each OS+Browser over the others of the same family')
  plt.ylabel('CDF')
  plt.xlabel('Prediction over other users\' learned model')
  plt.legend(['Windows+firefox', 'Windows+chrome', 'Linux+firefox', 'Linux+chrome'])
  plt.savefig('cdfallosandbrowserspredictions')
  #bloxplot for true positives
  if args.truep:
      plt.figure()
      plt.title('True Positives predictions, for each user of our detabase')
      plt.ylabel('Prediction')
      if args.compare:
          plt.boxplot([[v[8] for v in devicelist.values()], [v[9] for v in devicelist.values()]])
      else:
          plt.boxplot([v[8] for v in devicelist.values()])
      plt.savefig('boxplottruepositives')
  
  if args.roc:
    #Add ROC curvers for a global threshold and for a model-based interval
    range_gtresh = np.linspace(0, 1, 100)
    #don't forget to reverse()
    retain_fpos_r = 1
    retain_fpos_r_adv = 1
    retain_gthresh = 0
    retain_gthresh_adv = 0
    true_pos_r = []
    true_pos_r_adv = []
    false_pos_r = []
    false_pos_r_adv = []
    for g_thresh in range_gtresh:
      true_pos_r.append(0)
      true_pos_r_adv.append(0)
      false_pos_r.append(0)
      false_pos_r_adv.append(0)
      for email in devicelist:
        for other_user in devicelist:
          if email == other_user:
            #tpr 
            if devicelist[email][8] >= g_thresh:
              true_pos_r[-1]+=1
            if devicelist[email][9] >= g_thresh:
              true_pos_r_adv[-1]+=1
          else:
            #fpr
            if devicelist[email][6][other_user] >= g_thresh:
              false_pos_r[-1] += 1
            if devicelist[email][7][other_user] >= g_thresh:
              false_pos_r_adv[-1] += 1
      true_pos_r[-1] = float(true_pos_r[-1])/len(devicelist)
      true_pos_r_adv[-1] = float(true_pos_r_adv[-1])/len(devicelist)
      false_pos_r[-1] = float(false_pos_r[-1])/(len(devicelist)*(len(devicelist)-1))
      false_pos_r_adv[-1] = float(false_pos_r_adv[-1])/(len(devicelist)*(len(devicelist)-1))
      if true_pos_r[-1] == 1 and retain_fpos_r > false_pos_r[-1]:
          retain_fpos_r = false_pos_r[-1]
          retain_gthresh = g_thresh
      if true_pos_r_adv[-1] == 1 and retain_fpos_r_adv > false_pos_r_adv[-1]:
          retain_fpos_r_adv = false_pos_r_adv[-1]
          retain_gthresh_adv = g_thresh

    true_pos_r.reverse()
    false_pos_r.reverse()
    true_pos_r_adv.reverse()
    false_pos_r_adv.reverse()
    plt.figure()
    plt.xlim(xmax=0.2)
    plt.axvline(x = retain_fpos_r, linestyle="--", color="k")
    plt.axvline(x = retain_fpos_r_adv, linestyle="--", color="k")
    print "best global threshold for first arch: {0}".format(retain_gthresh)
    print "best global threshold for second arch: {0}".format(retain_gthresh_adv)
    #plt.title('ROC curve when a global threshold for authentication acceptance varries')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    arch1, = plt.plot(false_pos_r, true_pos_r, label="Arch 1")
    arch2, = plt.plot(false_pos_r_adv, true_pos_r_adv, label="Arch 2")
    plt.legend(handles=[arch1, arch2])
    plt.savefig('roc_gthresh')





  sys.exit(0)
