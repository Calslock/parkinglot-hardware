from skimage.measure import structural_similarity as ssim
import subprocess
import cv2
import time
import numpy as np
import imutils
import re
import pytesseract as pyt
import RPi.GPIO as GPIO
import requests as req

photo_delay = 2
barrier_delay = 10
config = r'--oem 3 --psm 11 -c tessedit_char_whitelist=ACEFGHJKLMNPQRSTUVWXY0123456789 -c language_model_penalty_non_freq_dict_word=1 -c language_model_penalty_non_dict_word=1'

GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.OUT, initial=GPIO.LOW)

def recog():
    time.sleep(photo_delay)
    subprocess.call("raspistill -o /home/pi/hires.jpg -w 1920 -h 1080 -n")
    img = cv2.imread("/home/pi/hires.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 15, 15, 15)
    edges = cv2.Canny(gray, 30, 200)
    contoured = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contoured)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
    foundContour = None
    for i in contours:
        perimeter = cv2.arcLength(i, True)
        approxd = cv2.approxPolyDP(i, 0.018 * perimeter, True)
        if len(approxd) == 4:
            foundContour = approxd
            break

    if foundContour is None:
        found = False
        print("No licence plate detected")
    else:
        found = True

    if found:
        cv2.drawContours(img, [foundContour], -1, (0, 0, 255), 3)

        # if contour is found draw mask around it
        mask = np.zeros(gray.shape, np.uint8)
        masked = cv2.drawContours(mask, [foundContour], 0, 255, -1)
        masked = cv2.bitwise_and(img, img, mask=mask)

        (x, y) = np.where(mask == 255)
        cropped = gray[np.min(x):np.max(x) + 1, np.min(y):np.max(y) + 1]

        ocr = pyt.image_to_string(cropped, config=config)
        ocr = ocr.replace(":", " ").replace("-", " ").replace("\n", "")
        reocr = re.search(r'([A-Z0-9]){2,3}\s{1}([A-Z0-9]){4,5}', ocr)
        if reocr is None:
            reocr = re.search(r'([A-Z0-9]){2,3}([A-Z0-9]){4,5}', ocr)
        print(reocr)
        recognized = reocr.group(0)
        recognized = recognized.replace(" ", "")
        return recognized

subprocess.call("raspistill -o /home/pi/im1.jpg -w 640 -h 480 -n")
while True:
    time.sleep(photo_delay)
    subprocess.call("raspistill -o /home/pi/im2.jpg -w 640 -h 480 -n")
    image1 = cv2.imread("/home/pi/im1.jpg")
    image2 = cv2.imread("/home/pi/im2.jpg")
    s = ssim(image1, image2)
    if s < 0.6:
        license = recog()

        url = 'http://localhost:9000/parkinglot-management-system/auth/signin'
        data = '{"username": "rpi@rpi.com", "password": "rpirpirpi"}'
        headers = {'Content-type': 'application/json'}
        logindata = req.post(url, data=data, headers=headers)

        token = (logindata.json()["accessToken"])
        url = 'http://localhost:9000/parkinglot-management-system/api/owners/cars'
        headers = {'Authorization': 'Bearer ' + token}

        list = []
        response = req.get(url, headers=headers)
        for i in response.json():
            if license == i["licenseNumber"]:
                GPIO.output(2, GPIO.HIGH)
                time.sleep(barrier_delay)
                GPIO.output(2, GPIO.LOW)

        subprocess.call("rm /home/pi/hires.jpg")

    subprocess.call("rm /home/pi/im1.jpg")
    subprocess.call("mv /home/pi/im2.jpg /home/pi/im1.jpg")
