# SWAT: Seamless Web Authentication Technology (published in the security and privacy track of WWW2019)

This repository holds the django module that demonstrates SWAT as well
as a few scripts written to experiment the idea. A demonstrator of SWAT
currently run at https://perceval.elen.ucl.ac.be  
  
The core idea of SWAT is to provide a seamless challenge-response
authentication protocol which leverages on the variation of html5 canvas
rendering made by the software and hardware stacks. After a training
phase that leads to featurer extraction with deep learning techniques, a
server becomes able to authenticate a user based on fresh canvasses,
hencee avoiding replay attacks. The whole authentication process is
natively supported by any mainstream browser, stateless on client
side and can be transparent to the user. We argue that those
features facilitate deployment and composition with other
authentication mechanisms without lowering the user experience.  
  

Paper link: soon.  
  
You may register, and try out to authenticate on
https://perceval.elen.ucl.ac.be/authenticate when the learning
phase finishes (the server is a rookie one, so be patient :-)
  
On the meantime, you may try to authenticate using the credential of my
laptop: florentin.rochet@stealth.com. For the majority of you, it should
outputs a small prediction (close to 0) that you're me, hopefully. And if it outputs
a prediction arround 0.99, then congrat, you're me :)

