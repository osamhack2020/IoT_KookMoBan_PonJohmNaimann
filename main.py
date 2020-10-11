# sudo apt-get install libzbar0

import numpy as np
import time
import pickle
import json

import requests
from pyzbar import pyzbar
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
import PIL.ImageOps


# SENSOR & ACTUATOR IO FUNCTION
def weight_isNow():     # Read weight sensor.

    return 0

def btn_recvPhone():    # Check if receive phone button is pushed.
    return False

def camera_takePhoto(): # From camera, take photo and return the photo.
    result = None

    '''
    TEMPORARILY PC CAPTURE
    '''
    from PIL import ImageGrab
    
    return ImageGrab.grab()

def make_doorLock():    # Check if door is closed, and lock. If door is not closed so failed to lock, return false.

    return True

def make_doorUnlock():  # Unlock Door

    return True


# CONSTANTS
SERVER_URL      = 'http://riyenas0925.iptime.org'
SERVER_MAXTRY   = 3
TOTP_DELAY      = 10


# PUBLIC VARIABLES
phone_isFull    = False

door_isOpen     = True

weight_saved    = 0
weight_err      = 0.05


# UTIL FUNCTIONS
def server_connect():
    print("Check Server Connection.")

    nowtry = 1
    while nowtry <= SERVER_MAXTRY:
        resp = requests.get(SERVER_URL)
        if resp.status_code != 200:
            print("    Server doesn't respond... (", nowtry, "/", SERVER_MAXTRY, ")")
            if nowtry == SERVER_MAXTRY:
                print("Failed to Connect Server. Operating as a Offline Mode.")
                return False
            else:
                time.sleep(5)
            nowtry += 1
        else:
            print("Server Connected!")
            return True

def server_returnPhone(id, TOTP, time):

    now = np.floor(time * 1000)
    params = {'timeInMillis': now, 'deviceId': id, 'expectedTOTP': TOTP}
    response = requests.post(url=SERVER_URL+'/api/totp/valid', data=json.dumps(params), headers={'Content-Type': 'application/json'})

    return response
            
def time_isForUse():
    result = False
    # Online Mode
    if server_isConnected:
        canUse = requests.get(SERVER_URL+'/')
        if canUse == 'True':
            result = True
    # Offline Mode
    else:
        time_now = time.localtime(time.time())
        nt = time_now.tm_hour*60 + time_now.tm_min
        # Weekend
        if time_now.tm_wday == 5 or time_now.tm_wday == 6:
            start_hour = 8
            start_minute = 0
            end_hour = 21
            end_minute = 0
        # Weekday
        else:
            start_hour = 17
            start_minute = 30
            end_hour = 21
            end_minute = 0

        start_time = start_hour*60 + start_minute
        end_time = end_hour*60 + end_minute
        if start_time < nt and nt < end_time:
            result = True
                
    return result

def qr_decrypt(photo, type):  # Decrypt photo

    return photo

def qr_read(photo): # Detect QR Code from photo, then return serial.
    result = ''

    return result



# RUN PROGRAM
# Check Server Connection
server_isConnected = server_connect()
        
# Check Self Status (using pickle)
with open('phone_isFull.pickle', 'wb') as fw:
    data = pickle.load(fw)
if data == 'isFull':
    phone_isFull == True
else: 
    phone_isFull == False

# Main Loop

while True:
    if phone_isFull:    # ANTI-THEFT
        # Check If GetPhone Button is Pushed
        if btn_recvPhone() and time_isForUse():
            make_doorUnlock()
        

    else:
        # Check If Weight Sensor Has Changed
        if abs(weight_saved - weight_isNow()) < weight_saved * weight_err:   
            # Nothing Happend
            adj = 0.95
            weight_saved = weight_saved * adj + weight_isNow() * (1-adj)
            pass
        else:
            # Something Entered
            weight_temp = weight_isNow()
            
            #   Then Filter Noise Case
            time.sleep(0.5)
            if abs(weight_saved - weight_isNow()) < (weight_saved * weight_err):
                break
            else:
                weight_saved = weight_isNow()
            
            #   Wait for next TOTP, take photo
            time.sleep(TOTP_DELAY)
            qr = qr_read(qr_decrypt(camera_takePhoto(), 'time-based onbasis'))
            if qr != '':
                # If QR Code Detected, request server phone return
                qr = json.loads(qr)
                success = server_returnPhone(qr['devicdId'], qr['totp'], time.time())
                if success:
                    # If good return case
                    # Request server: phone return log
                    pass
                else:
                    # If bad return case
                    # blah blah...
                    pass

