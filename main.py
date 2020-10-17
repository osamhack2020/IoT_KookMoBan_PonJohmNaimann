# sudo apt-get install libzbar0
# pip install opencv-python

import RPi.GPIO as gp
import picamera
import serial

import numpy as np
import time
import pickle
import json
import copy
import base64

import requests
from pyzbar import pyzbar
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
import PIL.ImageOps

import cv2


##======================= CONSTANTS =======================##

SERVER_URL      = 'https://osam.riyenas.dev'
SERVER_MAXTRY   = 3
TOTP_DELAY      = 10

PIN_RECVPHONE	= 36
PIN_DOORCLOSE0	= 38
PIN_DOORCLOSE1	= 40
PIN_SERVO0 		= 11
PIN_SERVO1		= 13
PIN_LEDLIGHT	= 16

SERVO_MIN_DUTY	= 3
SERVO_MAX_DUTY	= 12

#TEMPORARY
PIN_WEIGHT		= 37


##======================= GPIO INIT =======================##

gp.setmode(gp.BOARD)
gp.setup(PIN_RECVPHONE, gp.IN)
gp.setup(PIN_DOORCLOSE0, gp.IN)
gp.setup(PIN_DOORCLOSE1, gp.IN)
gp.setup(PIN_SERVO0, gp.OUT)
gp.setup(PIN_SERVO1, gp.OUT)
gp.setup(PIN_WEIGHT, gp.IN)

servo0 = gp.PWM(PIN_SERVO0, 50)
servo1 = gp.PWM(PIN_SERVO1, 50)
servo0.start(0)
servo1.start(0)

ser = serial.Serial('/dev/ttyUSB0', 9600)


##==================== PUBLIC VARIABLES ====================##

server_isConnected = False

phone_isFull    = False

door_isOpen     = True

weight_saved    = 0
weight_err      = 0.05

admin_id        = 0


##============== SENSOR & ACTUATOR IO FUNCTION ==============##

def weight_isNow():     # Read weight sensor.
    '''read loadcell input'''
    ser.write('weight'.encode('ascii'))
    buffer = ''
    while True:
        temp = ser.read().decode('ascii')
        if temp == '\n':
            break
        else:
            buffer += temp
    weight = 1023 - int(buffer)
    if weight < 0:
        weight = 0
    return weight

def btn_recvPhone():    # Check if receive phone button is pushed.
    '''read button input'''
    return gp.input(PIN_RECVPHONE)

def camera_takePhoto(): # From camera, take photo and return the photo.
    with picamera.PiCamera() as camera:
        camera.start_preview()
        camera.capture('capture.jpg')
        camera.stop_preview()
    img = Image.open('capture.jpg')
    return img

def setServoPos(servo, degree):
    if degree > 180:
        degree = 180
    
    duty = SERVO_MIN_DUTY+(degree*(SERVO_MAX_DUTY-SERVO_MIN_DUTY)/180.0)
    servo.ChangeDutyCycle(duty)

door_openSpeed = 0.01
def make_doorLock():    # Check if door is closed, and lock. If door is not closed so failed to lock, return false.
    print('Lock Door...')

    # Close Door
    for i in range(90):
        angle = (90-i)
        '''write angle'''
        setServoPos(servo0, angle)
        time.sleep(door_openSpeed)
    if weight_isNow() <= (3+weight_saved*weight_err):
        # If Sth Strange
        angle = 90
        '''write angle'''
        setServoPos(servo0, angle)
        print('Sth Strange!')
        print('Failed to Lock Door.\n')
        return False
    
    # Lock Locker
    '''Lock Locker'''
    setServoPos(servo1, 90)
    
    print('Successfully Locked Door.\n')
    return True

def make_doorUnlock():  # Unlock Door
    print('Open Door...')

    # Unlock Locker
    '''Unlock Locker'''
    setServoPos(servo1, 0)

    # Open Door
    for i in range(90):
        angle = i
        '''write angle'''
        setServoPos(servo0, angle)
        time.sleep(door_openSpeed)
    
    print('Successfully Opened Door.\n')
    return True



##========================= UTIL FUNCTIONS =========================##

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

def time_isForUse():
    result = False
    # Online Mode
    if server_isConnected:
        params = {'adminId': admin_id, 'millis': int(time.time())}
        canUse = requests.get(SERVER_URL+'/api/soldier/return/time/valid', params=params)
        if canUse.text == 'true':
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

def qr_decrypt(photo, key_vector):  # Decrypt photo
    new_img = copy.deepcopy(photo)
    new_img = new_img.resize((512,288))

    # Blur
    # new_img = cv2.blur(new_img, (5,5))

    # Generate o.n.basis with key vector
    e1 = np.array([1,0,0])
    e2 = np.array([0,1,0])
    e3 = np.array([0,0,1])

    u1 = np.array(key_vector)
    u1 = u1 / np.linalg.norm(u1)

    u2 = e2 - np.dot(e2, u1) / np.dot(u1, u1) * u1
    u2 = u2 / np.linalg.norm(u2)

    u3 = e3 - np.dot(e3, u1) / np.dot(u1, u1) * u1 - np.dot(e3, u2) / np.dot(u2, u2) * u2
    u3 = u3 / np.linalg.norm(u3)

    key_basis = np.array([u1, u2, u3]).T

    adjust = 220
    for i in range(new_img.size[0]):
        for j in range(new_img.size[1]):
            pixel = np.array(new_img.getpixel((i, j)))
            pixel = (pixel - 127) * adjust / 127
            pixel = np.dot(np.linalg.inv(key_basis), pixel)
            pixel = pixel + np.array((127, 127, 127))
            pixel = pixel.astype(int)
            new_img.putpixel((i,j), (pixel[0], pixel[0], pixel[0]))
    new_img = PIL.ImageOps.invert(new_img)
    new_img.save('decrypted.jpg')

    return new_img

def qr_read(photo): # Detect QR Code from photo, then return serial.
    result = ''
    
    decoded = pyzbar.decode(photo)
    if len(decoded) > 0:
        result = decoded[0].data.decode('utf-8')
    return result

#test_img = Image.open('test.png')
#print(qr_read(qr_decrypt(test_img, [-0.787984  ,  0.55249453,  0.27171862])))
#qr_decrypt(test_img, [-0.787984  ,  0.55249453,  0.27171862]).show()

#tempimg = cv2.imread('img/IMG_0289.jpg')

def sort_points(points):

    points = points.astype(np.float32)
    new_points = np.zeros((4, 2), dtype = "float32")
 
    s = points.sum(axis = 1)
    min_index = np.argmin(s)
    new_points[0] = points[min_index]
    points = np.delete(points, min_index, axis = 0)

    s = points.sum(axis = 1)
    max_index = np.argmax(s)
    new_points[2] = points[max_index]
    points = np.delete(points, max_index, axis = 0)

    if points[0][1] > points[1][1]:
        new_points[1] = points[1]
        new_points[3] = points[0]
    else:
        new_points[1] = points[0]
        new_points[3] = points[1]
 
    return new_points

def transform(img_input, points, size):

    points = sort_points(points)
    topLeft, topRight, bottomRight, bottomLeft = points
 
    maxWidth = size[0]
    maxHeight = size[1]
 
    
    dst = np.array([[0, 0],[maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],[0, maxHeight - 1]],
        dtype = "float32")
 

    H = cv2.getPerspectiveTransform(points, dst)
    img_warped = cv2.warpPerspective(img_input, H, (maxWidth, maxHeight))
 
    return img_warped

def phone_autoCut(photo):
    # Make photo into numpy.ndarray
    if type(photo) == str:
        new_img = cv2.imread(photo, cv2.IMREAD_COLOR)
    elif type(photo) == Image.Image or type(photo) == PIL.JpegImagePlugin.JpegImageFile:
        new_img = np.array(photo)
    elif type(photo) == np.ndarray:
        new_img = copy.deepcopy(photo)
    
    try:
        # Resize & Rotate
        height, width , channel = new_img.shape
        new_width = 540
        new_height = int(height * new_width/width)
        new_img = cv2.resize(new_img, dsize=(new_width, new_height), interpolation=cv2.INTER_AREA)
        #new_img = cv2.rotate(new_img, cv2.ROTATE_90_CLOCKWISE)
    except:   
        pass
    if True:
        # Grayscale
        gray_img = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('gray', gray_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Negative & Threshold
        gray_img = cv2.bitwise_not(gray_img)
        ret, gray_img = cv2.threshold(gray_img, 100, 255, cv2.THRESH_BINARY)
        # cv2.imshow('gray', gray_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Find Contours
        img, cont, hier = cv2.findContours(gray_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_area = 0
        max_index = 0
        for i in range(len(cont)):
            area = cv2.contourArea(cont[i])
            if area > max_area:
                max_area = area
                max_index = i
        max_cont = cont[max_index]
        temp_img = copy.deepcopy(new_img)
        cv2.drawContours(temp_img, [max_cont], -1, (0,255,0), 3)
        # cv2.imshow('gray', temp_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        
        # Dilation
        mask = np.zeros(gray_img.shape, np.uint8)
        mask = cv2.drawContours(mask, [max_cont], -1, (255,255,255), 5)
        kernel = np.ones((30,30), np.uint8)
        dilated = cv2.dilate(mask, kernel, iterations=1)
        img, cont, hier = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_area = 0
        max_index = 0
        for i in range(len(cont)):
            area = cv2.contourArea(cont[i])
            if area > max_area:
                max_area = area
                max_index = i
        max_cont = cont[max_index]
        # cv2.imshow('gray', dilated)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Approx
        epsilon = 0.1 * cv2.arcLength(max_cont, True)
        approx = cv2.approxPolyDP(max_cont, epsilon, True)

        # Convex Hull
        hull = cv2.convexHull(approx)
        temp_img = copy.deepcopy(new_img)
        cv2.drawContours(temp_img, [hull], -1, (0,0,255), 3)
        # cv2.imshow('gray', temp_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Hull Size Calc
        lines = []
        for i in range(len(hull)):
            lines.append(np.linalg.norm(hull[i][0] - hull[(i+1)%len(hull)][0]))
        lines.sort()
        # print(lines)

        # Front View
        points = []
        for p in hull:
            points.append(p[0])
        points = np.array(points)

        img_phone = transform(new_img, points, (int(lines[1]), int(lines[3]*1.2)))
        # cv2.imshow('gray', img_phone)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        return img_phone

    #except Exception as e:
    #    print('Failed to Autocut...')
    #    print(e)
    #    return new_img
temp_img = phone_autoCut('img/IMG_0301.jpg')
cv2.imwrite('autocut.jpg', temp_img)

def img_to_base64(img):
    return base64.b64encode(img)
# print(img_to_base64(temp_img))

def server_returnValid(id, TOTP, time):
    now = np.floor(time * 1000)
    params = {'timeInMillis': now, 'deviceId': id, 'expectedTOTP': TOTP}
    response = requests.post(url=SERVER_URL+'/api/totp/valid', data=json.dumps(params), headers={'Content-Type': 'application/json'})

    return response

def server_returnLog(id, returnTime, weight):
    cv2.imwrite('cam.jpeg', phone_autoCut(camera_takePhoto()))
    with open('cam.jpeg', 'rb') as img:
        photo_str = 'data:image/jpeg;base64,'+str(base64.b64encode(img.read()).decode('utf-8'))
    params = {'deviceId': id, 'returnTime': np.floor(returnTime*1000), 'weight': weight, 'photo': photo_str}
    # params = {'photo': photo_str}
    
    result = requests.post(url=SERVER_URL+'/api/soldier/device/log/create', data=json.dumps(params), headers={'Content-Type': 'application/json'})
    return result

# print(server_returnLog(1, time.time(), 100))



##========================= RUN PROGRAM =========================##


# Check Server Connection

server_isConnected = server_connect()
print()


# Check Self Status (using pickle)

with open('save.pickle', 'rb') as fr:
    data = pickle.load(fr)
if data['phone_isFull'] == True:
    print('Tray Check: Sth Already Inside.\n')
    phone_isFull = True
    weight_saved = data['weight']
    admin_id = data['adminId']
else:
    print('Tray Check: Nothing Inside.\n')
    phone_isFull = False


# Main Loop

print('Start Main Loop.')
while True:
    print('weight: ', weight_isNow(), '/', weight_saved)

    if phone_isFull:    # ANTI-THEFT
        # Check If GetPhone Button is Pushed
        if btn_recvPhone():
            print('Receive Phone Button Pressed!')
            if time_isForUse():
                make_doorUnlock()
                # Change Status
                phone_isFull = False
                weight_saved = 0
                admin_id = 0
                print('    Changed Status.')
                # Save Status
                temp_save = {'phone_isFull': phone_isFull, 'weight': weight_saved, 'adminId': admin_id}
                with open('save.pickle', 'wb') as fw:
                    pickle.dump(temp_save, fw)
                print('    Status Saved.')
                print('    Please Take Out the Phone.')
                time.sleep(10)
            else :
                print('But Not Time for Use!')
        

    else:
        # Check If Weight Sensor Has Changed
        if abs(weight_saved - weight_isNow()) <= (3+weight_saved * weight_err):
            # Nothing Happend
            pass
        else:
            # Something Entered
            print('Weight Sensor Activated!')
            weight_temp = weight_isNow()
            print('weight: ', weight_temp)
            
            #   Then Filter Noise Case
            time.sleep(0.5)
            if abs(weight_saved - weight_isNow()) <= (3+weight_saved * weight_err):
                print(' -> was an noise case.')
                continue
            else:
                print(' -> sth entered in the tray.')
            
            #   Lock Door
            door_maxtry = 3
            door_locked = False
            for i in range(door_maxtry+1):
                if make_doorLock():
                    door_locked = True
                    print('    Door Locked.')
                    break
                else:
                    print('    Door Cannot be Locked!')
            if not door_locked:
                print('Return Canceled: Door Problem!')
                make_doorUnlock()
                continue
            
            #   Wait for next TOTP, take photo
            print('    Reading QR Code...')
            return_time = time.time()
            time.sleep(TOTP_DELAY)
            qr = qr_read(qr_decrypt(camera_takePhoto(), [1,0,0]))

            if qr != '':
                # If QR Code Detected, request server phone return
                try:
                    qr = json.loads(qr)
                    success = server_returnValid(qr['deviceId'], qr['totp'], return_time)
                except:
                    success = False
                if success:
                    # If good return case
                    print('    Valid QR Code!')

                    # Measure weight properly
                    mean_weight = weight_isNow()
                    for i in range(10):
                        mean_weight = mean_weight * i/(1+i) + weight_isNow() /(1+i)
                        time.sleep(0.05)
                    print('    Weight: %f gram', mean_weight)

                    # Change Status
                    phone_isFull = True
                    weight_saved = mean_weight
                    admin_id = qr['adminId']
                    
                    # Save Status
                    temp_save = {'phone_isFull': True, 'weight': weight_saved, 'adminId': admin_id}
                    with open('save.pickle', 'wb') as fw:
                        pickle.dumps(temp_save, fw)
                    print('    Status Saved.')

                    # Request server: phone return log
                    server_returnLog(qr['deviceId'], return_time, weight_isNow())
                    print('    Sent Server Return Log.')

                    # Notice User Successful Phone Return
                    print('Return Finished Successfully.')

                    time.sleep(3)

                else:
                    # If bad return case
                    
                    # Alert User
                    print('Return Canceled: Invalid QR Code.')
                    
                    # Open Door
                    make_doorUnlock()
                    
                    # Wait Till Phone is Out
                    while weight_isNow() > 5:
                        time.sleep(1)
                    time.sleep(10)

            else:
                # No QR Code
                print('Return Failed: QR Reading Failed.')
                
                # Open Door
                make_doorUnlock()
                
                # Wait Till Phone is Out
                while weight_isNow() > 5:
                    time.sleep(1)
                time.sleep(10)
