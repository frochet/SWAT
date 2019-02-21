import sys, os
import fcntl
import sqlite3 as lite
import pdb
import shutil

"""
This script is executed every few minutes to check if any new user registered
on the website. If any did, then the convnet.py script is launched and do
a learning phase for that user

If the script is still executing the previous cron call, then it should raise an exception
using a file lock: the lock should be released when the previous call finished
"""


if __name__ == "__main__":
  f = open('lock', 'w')
  try:
    fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except IOError, e:
    print "busy"
    sys.exit(-1)
  
  # Look for a user to learn and call convnet
  
  # get all email:
  sqlpath = "/home/www-data/canvasauth/db.sqlite3"
  basepath = "/home/www-data/canvasauth/script/"
  
  connection = lite.connect(sqlpath)
  c = connection.cursor()
  c.execute('SELECT email, authc_computer.id FROM auth_user, authc_computer, authc_canvas\
             WHERE authc_computer.user_id_id = auth_user.id AND authc_computer.id = authc_canvas.computer_id_id\
             GROUP BY authc_computer.id\
	     HAVING COUNT(*) >= 2000')
  results= c.fetchall()
  c.close()
  firstemailok = ""
  badcomps = []
  with open(basepath+"wrongcomplist", "r") as wrongcomps:
    for line in wrongcomps:
        badcomps.append(int(line[:-1])) #remove \n
  for (email, compid) in results:
    filepath = basepath+"models/{0}compid{1}.h5"\
    .format(email.replace("@", "").replace(".",""), compid)
    if not os.path.isfile(filepath) and compid not in badcomps:
      firstemailok = email
      break
  if firstemailok == "":
      f.close()
      sys.exit(0)
  #we do the learning on firstemailok
  print "Learning for {0}".format(firstemailok)
  retvalue = ""
  retvalue = os.system("python /home/www-data/canvasauth/script/convnet.py --db {0} --email {1} --compid {2} --max_epoch 100 --store --advanced_arch --filepath_model models --filepath_hist history".format(sqlpath, firstemailok, compid)) >> 8
  if retvalue == 255: # convnet exit(-1)
      with open(basepath+"wrongcomplist", "a") as badcomps:
          badcomps.write("{0}\n".format(compid))
  else:
      shutil.copy(filepath, "/home/www-data/canvasauth/authc/models")
  
  f.close()
  sys.exit(0)
