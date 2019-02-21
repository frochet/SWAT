from django.shortcuts import render
from django.template import loader
import json, random
import os

from django.http import HttpResponse, HttpResponseRedirect
from .forms import LoginForm, CheckFpForm, UpdateCanvasForm, RegisterForm
from django.contrib.auth.models import User
from .models import Computer, Canvas
from django.core.exceptions import ObjectDoesNotExist
from django_user_agents.utils import get_user_agent
import keras
from keras.models import load_model
import subprocess
import numpy as np

CANVASVERSION = 1
def index(request, errorMessage=None, infoMessage=None):
    #Return simple login fora
    form = RegisterForm()
    action = '/participate/'
    return render(request, 'authc/index.html', {'form':form,
        'action':action, 'valueSubmit':"Participate",
        'errorMessage':errorMessage, 'infoMessage':infoMessage})


def participate(request):
    form = RegisterForm(request.POST)
    if form.is_valid():
        return render(request, 'authc/canvas.html', {'errorMessage':None, 'infoMessage':None,
            'email':request.POST['email']})
    return render(request, 'authc/index.html', {'form':form,
        'action':'/participate/', 'valueSubmit':'Participate',
        'errorMessage': "It seems that a least one form was not valid"})


def check_fp(request):
    form = CheckFpForm(request.POST)
    user_agent = get_user_agent(request)
    if form.is_valid():
        email = form.cleaned_data['email']
        fingerprint = form.cleaned_data['fingerprint']
        try:
            user = User.objects.get(email=email)
            try:
                computer = Computer.objects.get(user_id=user,
                        fingerprint=fingerprint)
                return HttpResponse(json.dumps({'errorType':1,
                    'errorMessage': "We already know you, please try again with another computer or another browser"}));
            except ObjectDoesNotExist:
                newComputer = Computer.objects.create(
                        user_id=user,
                        fingerprint=fingerprint,
                        os_family = user_agent.os.family,
                        browser_family = user_agent.browser.family,
                        is_mobile = user_agent.is_mobile,
			learned_val = -1)
                newComputer.save()
                return HttpResponse(json.dumps({'infoMessage':
                    "We are collecting the data. Thank you for adding one computer !"}));
        except ObjectDoesNotExist:
            #We never heard about this user
            try:
                computer = Computer.objects.get(fingerprint=fingerprint);
                return HttpResponse(json.dumps({'errorType':3,
                    'errorMessage': "We already know you with another email account on the same computer"}));
            except ObjectDoesNotExist:
                newUser = User.objects.create(email=email,
                    username=email)
                newComputer = Computer.objects.create(
                    user_id = newUser,
                    fingerprint=fingerprint,
                    os_family = user_agent.os.family,
                    browser_family = user_agent.browser.family,
                    is_mobile = user_agent.is_mobile,
		    learned_val = -1)
                newComputer.save()
                newUser.save()
                return HttpResponse(json.dumps({'infoMessage':
                "We are collecting the data. Thank you ! Go on /authenticate once finished!"}))
    else:
        return HttpResponse(json.dumps({'errorMessage':
            "", 'errorType':2}));

def canvas(request):
    return render(request, 'authc/canvas.html', {'logged':logged})

def update_canvas(request):
    form = UpdateCanvasForm(request.POST);
    if form.is_valid():
        email = form.cleaned_data['email']
        fingerprint = form.cleaned_data['fingerprint']
        canvasURLs = form.cleaned_data['canvasURL'].split(";-;")
        version = form.cleaned_data['version']
        try:
            user = User.objects.get(email=email)
            computer = Computer.objects.get(user_id=user,
                    fingerprint=fingerprint)
            for canvasURL in canvasURLs:
                if canvasURL.startswith("data") :
                    newCanvas = Canvas.objects.create(
                            computer_id=computer,
                            canvas=canvasURL,
                            version=version)
                    newCanvas.save()

            return HttpResponse(json.dumps({})) #everything ok
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps({'erroMessage':
                "Something wrong happened - Data collection stopped",
                'errorType':2}));
    else:
        return HttpResponse(json.dumps({'errorMessage':
            "Something wrong happened - Data collection stopped",
            'errorType':2}))
    

def authenticate(request):
    #generate some random texts
    def random_string(length):
        txt = ''
        alpha = 'abcdefghijklmnopqrstuvwxyz1234567890'
        for i in range(0, length):
            txt += random.choice(alpha)
        return txt
    texts = []
    for i in range(0, 32):
        texts.append(random_string(25))
    return render(request, 'authc/authenticate.html', {'form':LoginForm(),
        'infoMessage':"Please authenticate",
        'errorMessage': '',
        'action':'/check_authentication/',
        'valueSubmit':'Let me in',
        'canvas_text':json.dumps({'canvas_text':texts}),
        'canvas_version': CANVASVERSION})

def check_authentication(request):
    form = UpdateCanvasForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        fingerprint = form.cleaned_data['fingerprint']
        canvasURLs = form.cleaned_data['canvasURL'].split(";-;")[:-1] #last is ""
        version = form.cleaned_data['version']
        #TODO: Check if it is likely the canvas we wanted
        #How ? Use the canvas API to draw locally the expected image and compare MSE. Not performed for this demo.
        try:
            user = User.objects.get(email=email)
            computers = Computer.objects.all().filter(user_id=user)
            for computer in computers:
                filepath = "/home/www-data/canvasauth/authc/models/{0}compid{1}.h5".format(email.replace("@", "").replace(".",""), computer.id)
                if os.path.isfile(filepath):
                    model = load_model(filepath)
                    c_to_evaluate = []
                    for canvas in canvasURLs:
                        c_to_evaluate.append(Canvas.canvas_to_numpy_array(canvas, 35, 280))
                    prediction = np.median(model.predict(np.array(c_to_evaluate)))
                    ## clear model
                    keras.backend.clear_session()
                    learnedval = computer.learned_val
                    ## Interval is tuned from the paper
                    # best interval size for first arch: 2*0.0854271356784
                    # best interval size for second arch: 2*0.0653266331658
                    if prediction > learnedval-0.0653266331658 and prediction < learnedval+0.0653266331658:
                        return HttpResponse(json.dumps({'infoMessage':
                            "Hoooowdy you! Successfull authentication with prediction {0}".format(prediction)}))
                else:
                    return HttpResponse(json.dumps({'errorMessage':
                    "Either you're not in the database or the learning phase is not finished yet. Please wait a few minutes, this is a rookie server"}))
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps({'errorMessage':
                "User does not exist in our database",
                'errorType':2}));
        return HttpResponse(json.dumps({'infoMessage':
            "Not successfully authenticated:  {0}".format(prediction)}))
    else:
        return HttpResponse(json.dumps({'errorMessage':
                "Something wrong happened - Authentication failed, form not valid",
                'errorType':2}));


