try:
	# import dependencies
	from selenium import webdriver
	from selenium.webdriver.common.by import By
	from selenium.webdriver.common.keys import Keys
	from selenium.webdriver.chrome.service import Service
	from PIL import Image, ImageCms, ImageFilter
	import numpy as np
	import pytesseract
	import cv2
	import time
	import os

	## Helper Functions

	def step1():
		# open webpage
		driver.get(URL)

		# save captcha
		imdata = driver.find_element(By.ID,"imgCaptcha")
		with open(path, 'wb') as file:
		    file.write(imdata.screenshot_as_png)

	def step2():
		# convert to inverted mask and save img_temp
		im = cv2.imread(path)
		gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
		thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
		horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
		Mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,horizontal_kernel, iterations=2)
		#Mask = cv2.bitwise_not(Mask)
		cv2.imwrite("old.png", Mask)

		# open img_temp and reinvert mask
		img = Image.open("old.png")
		img = img.convert("RGBA")
		datas = img.getdata()
		newData = []
		for item in datas:
		    if item[0] == 0 and item[1] == 0 and item[2] == 0:
		        newData.append((255, 255, 255, 0))
		    else:
		        newData.append(item)
		img.putdata(newData)

		# paste mask on img and save new_temp_img
		background = Image.open(path)
		background = background.convert("RGBA")
		background.paste(img,mask=img)
		background.save("new.png","PNG")

	def step3(im):
		im = Image.open(im) # open last saved img
		im = im.crop((5,5,115,35)) # crop it
		# conver image to extractable form elements (deffer captcha styles)
		rgb = ImageCms.createProfile(colorSpace='sRGB')
		lab = ImageCms.createProfile(colorSpace='LAB')
		transform = ImageCms.buildTransform(inputProfile=rgb, outputProfile=lab, inMode='RGB', outMode='LAB')
		lab_im = ImageCms.applyTransform(im=im, transform=transform)
		l, a, b = lab_im.split()
		im=l # select an element which is most extractable
		im = im.filter(ImageFilter.MinFilter(3)) # filter it
		result = pytesseract.image_to_string(im) # send it to ocr and save results to a variable
		l=[]
		l.append(result.strip())
		if l[0]==" " or l[0]=="" : # if result will be empty then it will do above steps again untill it gets the result
			step1()
			step2()
			l[0]=step3("new.png")
		return l[0] # return final result (maybe right or wrong)

	def step4(enroll,ans):
		# site automation 
		enr = driver.find_element(By.ID,"txtEnrollNo") # get enrollment no. text box
		captex = driver.find_element(By.ID,"CodeNumberTextBox") # get captcha text box
		enr.send_keys(enroll) # send (type) given enrollment number to text box
		captex.send_keys(ans) # send (type) extracted captcha text to text box
		captex.send_keys(Keys.RETURN) # return (ENTER)

		ere = driver.find_element(By.ID,"lblMSG").text
		if ere == "ERROR: Incorrect captcha code, try again." : 
			return "err"
		if ere == "No Data Found! Check Enrollment Number." : 
			return "nodata"

		name = driver.find_element(By.ID,"lblName").text
		ins = driver.find_element(By.ID,"lblInstName").text
		bra = driver.find_element(By.ID,"lblBranch").text
		l=driver.find_elements(By.XPATH, "//table[@id='grdv2']/tbody/tr[2]")
		l=tuple(l[0].text.split(" "))
		cpi,cgpa,tb = l[1],l[2],l[3]
		l=driver.find_elements(By.XPATH, "//table[@id='grdvLastExm']/tbody/tr[2]")
		l=tuple(l[0].text.split(" "))
		le = f"{l[0]} {l[1]} {l[2]} {l[3]} {l[4]} {l[5]} {l[6]}"
		dd,cb,spi = l[8],l[9],l[10]
		return [enroll,name,ins,bra,float(cpi),float(cgpa),int(tb),le,dd,int(cb),float(spi)]

	def loop():
		# just a loop through different enrollment numbers
		mynewlist = []
		for i in mylist :
			enroll = "{}".format(i)
			step1()
			step2()
			ans=step3("new.png")
			nr=step4(enroll,ans)
			if nr == "err" :
				mynewlist.append(enroll)
			elif nr == "nodata" :
				dfout.loc[len(dfout)] = [enroll,"nodata","-","-","-","-","-","-","-","-","-"]
			else :
				dfout.loc[len(dfout)] = nr
				print(enroll)
		return mynewlist

	# initiate webdriver and configure options
	co = webdriver.ChromeOptions()
	co.headless = True # for headless window (not visible in desktop)
	co.add_argument("--incognito") # for incognito mode

	# initiate chromedriver service by defining path (Choose chromedriver according to your chrome version)
	ser = Service("G:\\My Drive\\projects\\captcha_solver\\chromedriver.exe")
	driver = webdriver.Chrome(service=ser,options=co) # start webdriver

	# define url and filename for download captcha_temp
	URL = "https://www.students.gtu.ac.in/"
	path="cap.jpg"

	import pandas as pd
	dfin = pd.read_excel('g.xlsx')
	#mylist = dfin['ENRNO'].tolist() # take enrollment no. input from excel file
	mylist = range(190280111001,190280111200) # OR give range of enrollment no. (here i given our batch's range)
	dfout = dfin[0:0] # create empty dataframe for filling output data with same labels that input file has

	# main driver programm
	# loop runs untill all data has scraped if any server error not happens
	while 1:
		mynewlist=loop()
		if len(mynewlist) != 0:
			mylist = mynewlist
		elif len(mynewlist) == 0:
			break
	# save dataframe to excel file
	dfout.to_excel("out.xlsx")

finally:
	driver.close() # close the window
	driver.quit() # stop the driver
	# remove unnecessary files
	os.remove("cap.jpg")
	os.remove("old.png")
	os.remove("new.png")