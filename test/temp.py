from pyzbar import pyzbar
from PIL import ImageGrab
import requests
import json
import time
import numpy as np

img = ImageGrab.grab()

qr_data = json.loads(pyzbar.decode(img)[0].data.decode('utf-8'))
print(qr_data['deviceId'])
print(qr_data['totp'])

url = 'http://riyenas0925.iptime.org/api/totp/valid'

now = np.floor(time.time() * 1000)
print(now)

params = {'timeInMillis': now, 'deviceId': qr_data['deviceId'], 'expectedTOTP': qr_data['totp']}
response = requests.post(url=url, data=json.dumps(params), headers={'Content-Type': 'application/json'})

print(response.status_code)
print(response.text)