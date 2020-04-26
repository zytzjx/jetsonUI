
#!/usr/bin/python3
import cv2
from skimage.measure import compare_ssim
import numpy as np
import argparse
import os.path
import logging
import json
from datetime import datetime
import sys

logger = logging.getLogger('PSILOG')

def structural_sim(img_a, img_b):
  '''
  Measure the structural similarity between two images
  @args:
    {str} path_a: the path to an image file
    {str} path_b: the path to an image file
  @returns:
    {float} a float {-1:1} that measures structural similarity
      between the input images
  '''
  sim, diff = compare_ssim(img_a, img_b, full=True ) #multichannel = True)
  return sim


def globalAlignment(img1_color, img2_color):
    # Convert to grayscale.
    img1 = cv2.cvtColor(img1_color, cv2.COLOR_BGR2GRAY)   #image to be aligned
    img2 = cv2.cvtColor(img2_color, cv2.COLOR_BGR2GRAY)   #reference image
    height, width = img2.shape

    # Create ORB detector with 5000 features.
    orb_detector = cv2.ORB_create(500)

    # Find keypoints and descriptors.
    # The first arg is the image, second arg is the mask
    #  (which is not reqiured in this case).
    kp1, d1 = orb_detector.detectAndCompute(img1, None)
    kp2, d2 = orb_detector.detectAndCompute(img2, None)

    # Match features between the two images.
    # We create a Brute Force matcher with
    # Hamming distance as measurement mode.
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Match the two sets of descriptors.
    matches = matcher.match(d1, d2)

    # Sort matches on the basis of their Hamming distance.
    matches.sort(key=lambda x: x.distance)

    # Take the top 90 % matches forward.
    matches = matches[:int(len(matches) * 30)]
    no_of_matches = len(matches)

    if no_of_matches > 10:
        # Define empty matrices of shape no_of_matches * 2.
        p1 = np.zeros((no_of_matches, 2))
        p2 = np.zeros((no_of_matches, 2))

        for i in range(len(matches)):
            p1[i, :] = kp1[matches[i].queryIdx].pt
            p2[i, :] = kp2[matches[i].trainIdx].pt

        # Find the homography matrix.
        homography, mask = cv2.findHomography(p1, p2, cv2.RANSAC)

        # Use this matrix to transform the
        # colored image wrt the reference image.
        transformed_img = cv2.warpPerspective(img1_color,
                                            homography, (width, height))
    else:
        transformed_img = img1_color
    #cv2.imwrite('test_transformed.jpg', transformed_img)
    return transformed_img

def evaluateScrew(bigImage, roi_0, roi_1, roi_2, roi_3, imageTemplate):

    corrcoefScore = np.zeros(80)
    width = imageTemplate.shape[0]
    height = imageTemplate.shape[1]
    #roiList = []
    for i in range(80):
        rows, cols = bigImage.shape
        trans_range = 10
        # Translation
        tr_x = trans_range * np.random.uniform() - trans_range / 2
        tr_y = trans_range * np.random.uniform() - trans_range / 2
        ##Trans_M = np.float([[1, 0, tr_x], [0, 1, tr_y]])
        ##bigImg = cv2.warpAffine(bigImage, Trans_M, (cols, rows))
        new_roi_0 = int(roi_0 + tr_x)
        new_roi_1 = new_roi_0 + width
        new_roi_2 = int(roi_2 + tr_y)
        new_roi_3 = new_roi_2 + height
        if (new_roi_0 > 0 and new_roi_1 < cols and new_roi_2 >0 and new_roi_3 < rows):
            img = bigImage[new_roi_0: new_roi_1, new_roi_2: new_roi_3]
        else:
            img = bigImage[roi_0: roi_1, roi_2: roi_3]
        # Cross correlation coefficient
        A = np.array(imageTemplate)
        B = np.array(img)
        if A.shape == B.shape and np.std(A.ravel()) > 0.0000000001 and np.std(B.ravel()) > 0.0000000001:
            corrcoefScore[i] = np.corrcoef(A.ravel(), B.ravel())[0][1]
            #roiList.append([new_roi_0, new_roi_1, new_roi_2, new_roi_3])
        else:
            logger.error(A.shape)
            logger.error(B.shape)
            logger.error('Size of test screw does not match size of profile...')
            logger.error('Or std of A or B is 0')
            corrcoefScore[i] = 0
            #roiList.append([new_roi_0, new_roi_1, new_roi_2, new_roi_3])
    maxScore = max(corrcoefScore)
    #maxPos = np.argmax(corrcoefScore)
    #maxROI = roiList[maxPos]
    #print('max corrcoef:', maxScore)
    return maxScore

def testScrews(inputDeviceFileName, inputDeviceImageName, inputImageName):
    logger.info(datetime.now().strftime("%H:%M:%S.%f")+"  testScrews++")
    logger.info("arg0 "+inputDeviceFileName)
    logger.info("arg1 "+inputDeviceImageName)
    logger.info("arg2 "+inputImageName)
    # current image
    bigImage = cv2.imread(inputImageName)
    # template image
    ###templateImage = cv2.imread(inputDeviceImageName)
    # global alignment
    ###transformed_img = globalAlignment(bigImage, templateImage)
    transformed_img = bigImage
    # convert to gray images
    ###imageTemplateGray = cv2.cvtColor(templateImage, cv2.COLOR_BGR2GRAY)  # cv2.COLOR_BGR2GRAY
    imgGray = cv2.cvtColor(transformed_img, cv2.COLOR_BGR2GRAY)  # cv2.COLOR_BGR2GRAY

    # reading in the screw profile file
    # process each screw in the profile one by one
    resultList = []
    with open(inputDeviceFileName) as f:
        for line in f:
            words = line.split()
            screwTemplateImageName = words[0][:-1]
            #print(screwTemplateImageName)
            roi_0 = int(words[3][:-1])
            roi_1 = int(words[4])
            roi_2 = int(words[1][:-1])
            roi_3 = int(words[2][:-1])
            imageTemplate = cv2.imread(screwTemplateImageName)
            imageTemplate = cv2.cvtColor(imageTemplate, cv2.COLOR_BGR2GRAY)
            maxScore = evaluateScrew(imgGray, roi_0, roi_1, roi_2, roi_3, imageTemplate)
            if maxScore < 0.45: 
                resultList.append([maxScore, [roi_2, roi_3, roi_0, roi_1]])
    logger.info(datetime.now().strftime("%H:%M:%S.%f")+"  testScrews--")
    ##filtered_numbers = [number for number in numbers if number < 3]
    return resultList

'''
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
#ap.add_argument("-folderName", "-profile folder name", type=str, required=True,
#	help="folder name for screw profile")

ap.add_argument("-txtfilename", "-text file name", type=str, required=True,
	help="screw profile txt file name")
ap.add_argument("-jpgfilename", "-jpg file name", type=str, required=True,
	help="screw profile jpg file name")
ap.add_argument("-testImageName", "-test image name", type=str, required=True,
	help="test image name")
ap.add_argument("-result", "-result file.", type=str, required=False, 
    help="out put result file")
args = vars(ap.parse_args())

# for testing the 'testScrews' function...
#inputDeviceFileName = 'PSI' + '/' + args["folderName"] + '/' + args["folderName"] + '.txt'
#inputDeviceImageName = 'PSI' + '/' + args["folderName"] + '/' + args["folderName"] + '.jpg'
inputDeviceFileName = args["txtfilename"]
inputDeviceImageName = args["jpgfilename"]
inputImageName = args["testImageName"]
resultName=args["result"]
#print(inputDeviceImageName)
#print(inputImageName)
        
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if os.path.exists(inputDeviceFileName) and os.path.exists(inputDeviceImageName) and os.path.exists(inputImageName):
    logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call testScrews++")
    result = testScrews(inputDeviceFileName, inputDeviceImageName, inputImageName)
    logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call testScrews--")
    #print(result)
    if resultName is not None and resultName !="":
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call testScrews save++")
        with open(resultName, 'w') as outfile:
            json.dump(result, outfile)
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call testScrews save--")
    
    logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call testScrews end--")
else:
    print("Files are not read in...")

'''