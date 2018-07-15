#n!/usr/bin/env python
'''
Todo - Blocking

Todo 
Save to github
Do not run multiple instances
clear display after save
Implement scrolling (touch)
Implement Search

Do it later

Done
Edit in the main loop instead of box.edit()
Task longer than 1 line break the selection logic. truncate
	Fix the restriction on item length
	keep a lookup of index on page to index on file (multi lignes items)

Manage the archive
Priority toggle 0 1 2
Implement delete - require confirmation box
Button handlers
Read data from file and updte in list
Launcher or icon to launch program in termux
'''


import os
import glob
from datetime import *
import time
import platform
from shutil import copyfile
import curses 
import curses.textpad

rawTasks = []
task_list = []
firstRowListBox = 4
isCreateMode = True
newDueDate = ""
newItem = ""
msgItemCount = ""
J3Delta = 12
highlightText = 0
normalText = 0

#Not required - declared in main
#offset = 0
hlOffset = 5
#selectionIndex = 0

class TodoItem:
	"TodoItem class handles a single todo item"
	priority = 0
	text = ""
	#thisMorning = time.mktime(datetime(datetime.now().year, datetime.now().month, datetime.now().day).timetuple())
	#nextMorning = time.mktime((datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(days=1)).timetuple())
	thisMorning = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
	nextMorning = datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(days=1)

	#print("thisMorning is " + str(thisMorning))

	def __init__(self, dataLine):

		if (dataLine == ""):
			self.text = "" 
			self.priority = self.thisMorning

		else:
			#print("2-Creating a new task " + dataLine)
			tmpPriority = dataLine[0:15]
			tmpTask = dataLine[16:]

			self.priority = datetime(int(tmpPriority[0:4]), 
							 int(tmpPriority[4:6]), 
							 int(tmpPriority[6:8]), 
							 int(tmpPriority[9:11]), 
							 int(tmpPriority[11:13]), 
							 int(tmpPriority[13:15]))

			self.text = tmpTask

	def formattedString(self):
		formattedString = ""
		if (self.isPast()):
			formattedString = " - Passed item - " + self.text
		elif (self.isToday()):
			if (self.isHigh()):
				formattedString = "!! " + self.text
			elif (self.isMedium()):
				formattedString = "! " + self.text

			else:
				formattedString = " " + self.text
		else:	
			formattedString = str(self.priority)[0:10] + " - " + self.text
		return formattedString
		
	def toString(self):
		return	 self.priority.strftime("%Y%m%d-%H%M%S") + "-" + self.text
		
	def getPriorityAsText(self):
		return	 self.priority.strftime("%Y%m%d-%H%M%S")
		
	def isPast(self):
		return self.priority < self.thisMorning
 
	def isToday(self):
		return ((self.priority >= self.thisMorning) and (self.priority < self.nextMorning)) 
 
	def isHigh(self):
		return (self.priority.hour == 0) 
 
	def isMedium(self):
		return (self.priority.hour == 1) 
 
	def isLow(self):
		return (self.priority.hour > 1) 
			
 
	def setToday(self):
		self.priority = datetime.now() 

	def setHigh(self):
		self.priority = self.thisMorning
 
	def setMedium(self):
		self.priority = self.thisMorning + timedelta(hours=1)

	def setLow(self):
		self.priority = self.thisMorning + timedelta(hours=2)
 
	#def serialize(self):
		#pass		

	
	def init_priority(self):
		#self.currentItem.priority = datetime(self.currentItem.priority.year, self.currentItem.priority.month, self.currentItem.priority.day)
		#self.due_date_text_input = ority.insert(0, self.currentItem.priority.strftime("%Y%m%d-%H%M%S"))
		pass
		
	def setToday(self):
		self.currentItem.priority =  datetime.now()
		self.editPriority.delete(0, 64)
		self.editPriority.insert(0, self.currentItem.priority.strftime("%Y%m%d-%H%M%S"))

	def NextDay(self):
		self.priority =  self.priority + timedelta(days=1)
		#self.editPriority.delete(0, 64)
		#self.editPriority.insert(0, self.currentItem.priority.strftime("%Y%m%d-%H%M%S"))
	
	def NextSaturday(self):

		if ((date.weekday(self.priority)) == 5):
			self.priority = self.priority + timedelta(days=7)
		else:
			while ((date.weekday(self.priority)) != 5):
				self.priority = self.priority + timedelta(days=1)
	



tmpTodoItem = TodoItem("")

def refreshDisplay(offset, hlOffset):
		#print("Refresh at offset " + str(offset) + "\n")
		global boxList

		boxList.erase()

		#boxList.addstr("Refresh at offset " + str(offset) + "\n")
		for i in range(11): 
			if (i == hlOffset):
				boxList.addstr((task_list[offset + i].formattedString())[0:40] + "\n", highlightText)
			else:
				boxList.addstr((task_list[offset + i].formattedString())[0:40] + "\n")
			#print(task_list[offset + i].formattedString())
		boxList.refresh()

def initLayout():

	global boxTitle
	global boxDueDate
	global boxItem
	global boxList
	global boxDelete
	global boxSearch
	global boxPriMinus
	global boxScroll
	global boxNew
	global boxNextDay
	global boxNextSat
	global boxSave
	global txtTask
	global tmpTodoItem
	global highlightText
	global normalText

	screen = curses.initscr()
	curses.mousemask(1)
	curses.noecho() 
	curses.curs_set(0) 
	screen.keypad(1) 

	screen.border(0)
	curses.start_color()
	curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_CYAN)
	highlightText = curses.color_pair( 1 )
	normalText = curses.A_NORMAL

	boxTitle = curses.newwin(1, 45, 0, 0)
	boxDueDate = curses.newwin(1, 45, 1, 0)
	boxItem = curses.newwin(2, 45, 2, 0)
	txtTask = curses.textpad.Textbox(boxItem)
	#boxList = curses.newwin(25, 45, 4, 0)
	boxList = curses.newwin(12, 45, 4, 0)
	
	boxDelete = curses.newwin(4, 10, 28 - J3Delta, 0)
	boxSearch = curses.newwin(4, 10, 28 - J3Delta, 11)
	boxPriMinus = curses.newwin(4, 10, 28 - J3Delta, 22)
	boxScroll = curses.newwin(4, 10, 28 - J3Delta, 33)

	boxNew = curses.newwin(4, 10, 32 - J3Delta, 0)
	boxNextDay = curses.newwin(4, 10, 32 - J3Delta, 11)
	boxNextSat = curses.newwin(4, 10, 32 - J3Delta, 22)
	boxSave = curses.newwin(4, 10, 32 - J3Delta, 33)



	boxTitle.box()	
	boxTitle.addstr("Title")
	boxDueDate.box()	
	boxDueDate.addstr(tmpTodoItem.getPriorityAsText())
	boxItem.box()	
	#boxItem.addstr("Item")
	boxList.box()	

	boxDelete.box()
	boxDelete.addstr(1,2,"Delete")
	boxSearch.box()
	boxSearch.addstr(1,2, "Search")
	boxPriMinus.box()
	boxPriMinus.addstr(1,3, "Pri-")
	boxScroll.box()
	boxScroll.addstr(1,2, "Scroll")

	boxNew.box()
	boxNew.addstr(1,3,"New")
	boxNextDay.box()
	boxNextDay.addstr(1,1, "Next Day")
	boxNextSat.box()
	boxNextSat.addstr(1,1, "Next Sat")
	boxSave.box()
	boxSave.addstr(1,3, "Save")
	
	screen.refresh()

	boxTitle.refresh()
	boxDueDate.refresh()
	boxItem.refresh()
	boxList.refresh()

	boxDelete.refresh()
	boxSearch.refresh()
	boxPriMinus.refresh()
	boxScroll.refresh()

	boxNew.refresh()
	boxNextDay.refresh()
	boxNextSat.refresh()
	boxSave.refresh()

def refreshFromFile():
		#global items
		global displayItems
		global rawTasks
		global offset
		global hlOffset
		global hlOffset
		global task_list
		global tmpTodoItem
		global isCreateMode
		global newDueDate


		initLayout()
		#items = []
		totalItemsCount = 0
		todayItemsCount = 0
		urgentItemsCount = 0
		#mainDialog.listbox.delete(0, END)
		#print("Using file " + fullPathFileName)
		del rawTasks[0:]
		#del task_list.adapter.data[0:]
		task_list = []
		hanFile = open(fullPathFileName ,'r')
		for dataLine in hanFile:
			dataLine = dataLine[0: -1]
			if (dataLine != ""):
		#		items.append(dataLine)
				tmpTodoItem = TodoItem(dataLine)
				if (tmpTodoItem.isPast()):
					tmpTodoItem.priority = tmpTodoItem.priority + timedelta(days=1)
		
				while (tmpTodoItem.isPast()):
					tmpTodoItem.priority = tmpTodoItem.priority + timedelta(days=1)
		
				#items.append(tmpTodoItem.formatttedString())
				#task_list.adapter.data.extend([tmpTodoItem.formattedString()])
				task_list.append(tmpTodoItem)
				rawTasks.append(tmpTodoItem.toString())
				totalItemsCount = totalItemsCount + 1
	
		
				#mainDialog.listbox.insert(END, tmpTodoItem.formattedString())
				if (tmpTodoItem.isToday()):
					todayItemsCount = todayItemsCount + 1
					if (tmpTodoItem.isHigh()):
						#print 'High priority item'
						urgentItemsCount = urgentItemsCount + 1

			#else:
				#updateSatus("Skipping empty line")
	
		hanFile.close()
		tmpTodoItem = TodoItem("")
		updateStatus(" Item count - " + str(totalItemsCount) + " - Today items " + str(todayItemsCount) + " - " + str(urgentItemsCount)) 
		refreshDisplay(offset, hlOffset)
		isCreateMode = False
		newDueDate = tmpTodoItem.getPriorityAsText()


	


def manageArchive():

	if (platform.machine() == "i686"):
		archiveFile = "/home/rene/develop/python/kvTodo/Data/Todo-" + datetime.now().strftime("%Y%m%d-%H%M%S") 
		archivePath = "/home/rene/develop/python/kvTodo/Data/"
		globalArchiveFileName = "/home/rene/develop/python/kvTodo/Data/archive.txt"
	else:

		path = "/storage/sdcard0/Rene/Python/Data/"
		archivePath = "/storage/sdcard0/Rene/Python/Data/"
		archiveFile = "/storage/sdcard0/Rene/Python/Data/Todo-" + datetime.now().strftime("%Y%m%d-%H%M%S") 
		globalArchiveFileName = "/storage/sdcard0/Rene/Python/Data/Todo-archive.txt"


	copyfile(fullPathFileName, archiveFile)	

	archiveItems = []

	for file in os.listdir(archivePath):
		file = archivePath + file

		archiveFile = open(file ,'r')
		for dataLine in archiveFile:
			alreadyArchived = False
			dataLine = dataLine[0: -1]
			taskOnly = dataLine[16:]
			#print "Checking task " + dataLine
			for knownTask in archiveItems:	
				knownTask = knownTask[16:]
				#print "Comparing " + knownTask + " with " + taskOnly
				if knownTask == taskOnly:
				#		print "Skipping known task " +  dataLine
					alreadyArchived = True
					break
			if (alreadyArchived == False):
				#print "Archiving new task " +  dataLine
				archiveItems.append(dataLine)
		archiveFile.close()
	#print "Current file is " + str(file) + " " + str(os.stat(file).st_mtime)
	if (time.mktime(datetime.now().timetuple()) - os.stat(file).st_mtime > (30 * 24 * 3600)):
		print("Deleting file " + file + " "  + str(time.mktime(datetime.now().timetuple()) - os.stat(file).st_ctime))
		os.remove(file)
	#else:
			#print "Skipping file "  + file + " " + str(time.mktime(datetime.now().timetuple()) - os.stat(file).st_ctime)
			#pass


	print("Saving items to file " + globalArchiveFileName)
	archiveItems.sort()
	os.remove(globalArchiveFileName)
	globalArchiveFile = open(globalArchiveFileName ,'w')
	for item in archiveItems:
		globalArchiveFile.write(item + "\n")
	globalArchiveFile.close()



def updateStatus(msg):
	boxTitle.erase()
	boxTitle.addstr(0,0,msg[0:40])
	boxTitle.refresh()

def updateDueDate():
	global newDueDate
	global tmpTodoItem

	boxDueDate.erase()
	boxDueDate.addstr(tmpTodoItem.getPriorityAsText())
	boxDueDate.refresh()
	newDueDate = tmpTodoItem.getPriorityAsText()

def updateTask():
	global newItem
	global tmpTodoItem

	boxItem.erase()
	boxItem.addstr(tmpTodoItem.text)
	boxItem.refresh()
	newItem = tmpTodoItem.text

	#boxItem.addstr(tmpTodoItem.text)
	#result = txtTask.edit()
	#updateStatus("Edited text " + result)

def onDelete():
	global selecionIndex
	global tmpTodoItem

	updateStatus("Pressed Delete")
	cmdLine = "dialog --yesno \"Please confirm Deletion of task\n" + tmpTodoItem.getPriorityAsText() + "\n"  + tmpTodoItem.text + "\" 10 50"
	#updateStatus(cmdLine)
	#print(cmdLine + "\n")
	#print(cmdLine + "\n")
	#print(cmdLine + "\n")
	#print(cmdLine + "\n")
	#print(cmdLine + "\n")
	retVal = os.system(cmdLine)
	if (retVal == 0):
		updateStatus("Deleting task")
		del rawTasks[selectionIndex]
		saveToFile()
	else:
		updateStatus("NOT deleting task")
		saveToFile()


#def onSearch():
	#updateStatus("Pressed Search")
	#refreshFromFile()

def onNextDay():
	global newDueDate
	global tmpTodoItem


	tmpTodoItem.NextDay()
	updateDueDate()
	newDueDate = tmpTodoItem.getPriorityAsText()

def onNextSat():
	global newDueDate
	global tmpTodoItem
	tmpTodoItem.NextSaturday()
	updateDueDate()
	newDueDate = tmpTodoItem.getPriorityAsText()


def onPriMin():
	global tmpTodoItem

	if tmpTodoItem.isHigh():
		tmpTodoItem.setMedium()
	elif (tmpTodoItem.isMedium()):
		tmpTodoItem.setLow()
	elif tmpTodoItem.isLow():
		tmpTodoItem.setHigh()
	updateDueDate()

def onScroll():
	global offset
	if (offset + 5) < len(rawTasks):
		offset = offset + 5
		refreshDisplay(offset, hlOffset)

def onNew():
	global newDueDate
	global newItem
	global msgItemCount
	global isCreateMode
	global txtTask
	global tmpTodoItem

	updateStatus("Pressed New")
	isCreateMode = True
	#title_mode = "Create Task mode "
	#self.title_text.text = self.title_mode + " - " + self.title_count

	#msgItemcount = "0 " + str(len(rawTasks))
	tmpTodoItem = TodoItem("")

	boxDueDate.erase()
	boxDueDate.addstr(tmpTodoItem.getPriorityAsText())
	boxDueDate.refresh()
	
	boxItem.erase()
	boxItem.addstr(tmpTodoItem.text)
	boxItem.refresh()

	newItem = txtTask.edit()[0:-1].replace("\n", "-")
	updateStatus("Edited text " + newItem)
	newDueDate = tmpTodoItem.getPriorityAsText()
	#print("newDueDate1 is " + newDueDate)
	#msgItemcount = "1 " + str(len(rawTasks))


def onSave():
	global newDueDate
	global newItem
	global msgItemCount
	global selectionIndex
	global tmpTodoItem


	#updateStatus("Pressed Save")

	msgItemCount = str(len(rawTasks)) + " "


	#print("newDueDate2 is " + newDueDate)
	tmpDataLine = newDueDate + "-" + newItem
	#updateStatus("tmpDataLine - " + tmpDataLine)
	tmpTodoItem = TodoItem(tmpDataLine) 
	#updateStatus("tmpTodoItem - " + tmpTodoItem.text)
	msgItemCount = msgItemCount + str(len(rawTasks)) + " "

	if (newItem != ""):
		if (isCreateMode):
		
			updateStatus("Save new task " + tmpTodoItem.text)
			rawTasks.append(tmpDataLine)
			msgItemCount = msgItemCount + str(len(rawTasks)) + " "
		else:
			updateStatus("Update mode - Selection index is " + str(selectionIndex))
			rawTasks[selectionIndex] = tmpDataLine
		#updateStatus("item count - " + str(len(rawTasks)))
		saveToFile()

	else:
		updateStatus("Will not save an empty item")
	msgItemCount = msgItemCount + str(len(rawTasks)) + " "
	#updateStatus(msgItemCount)



def saveToFile():
	global fullPathFileName
	global msgItemCount


	msgItemCount = msgItemCount + str(len(rawTasks)) + " "
	manageArchive()	
	rawTasks.sort()

	msgItemCount = msgItemCount + str(len(rawTasks)) + " "
	outFile = open(fullPathFileName ,'w')
	for dataLine in  rawTasks:
		#print "Saving - " + dataLine
		outFile.write(dataLine + "\n")
		#updateStatus("Saving - " + dataLine)
	outFile.close()
	msgItemCount = msgItemCount + str(len(rawTasks)) + " "
	refreshFromFile()
	msgItemCount = msgItemCount + str(len(rawTasks)) + " "
	

if __name__ == "__main__":

	offset = 0
	selectionIndex = 0

	screen = curses.initscr()
	#print("Running on " + platform.machine())
	if (platform.machine() == "i686"):
		#print("Running on i686")
		path = "/home/rene/develop/python/"
	else:
		#print("NOT Running on i686")
		path = "/storage/sdcard0/Rene/Python/"


	app_folder = os.path.dirname(os.path.abspath(__file__))
	#print("App folder is " + app_folder)
	

	#items = []
	
	hanFileName = "Todo.txt"
	fullPathFileName = path + hanFileName
	#print("Using file " + fullPathFileName)
	
		


	try:

		initLayout()	
		refreshFromFile()
	
		while True:
			event = screen.getch() 
			if event == ord("q"): break 

			if event == ord("\n"): 
				selectionIndex = offset + hlOffset
				tmpTodoItem = task_list[selectionIndex]
				#updateStatus("Mouse event at " + str(mx) + " - " + str(my) + tmpTodoItem.toString())
				updateDueDate()
				updateTask()

				#newItem = txtTask.edit()[0:-1].replace("\n", "-")

			if ((event >= ord(" ")) and (event <= ord("~"))):
				newItem = newItem + chr(event)
				tmpTodoItem = TodoItem(newDueDate + "-" + newItem)
				updateDueDate()
				updateTask()
				#boxItem.addstr(str(chr(event)))
				#boxItem.refresh()

			if event == curses.KEY_DOWN:
				if hlOffset < 10:
					hlOffset = hlOffset + 1
					refreshDisplay(offset, hlOffset)
				elif offset < len(rawTasks):
					offset = offset + 1
					refreshDisplay(offset, hlOffset)

			if event == curses.KEY_UP:
				if hlOffset > 0:
					hlOffset = hlOffset - 1
					refreshDisplay(offset, hlOffset)
				elif offset > 0:
					offset = offset - 1
					refreshDisplay(offset, hlOffset)

 
			if event == curses.KEY_MOUSE:
				_, mx, my, _, _ = curses.getmouse()
				y, x = screen.getyx()
				#boxList.addstr(y, x, screen.instr(my, mx, 5))
				#boxList.addstr("Mouse event at " + str(mx) + " - " + str(my) + "\n\n")
				#boxList.addstr("Fifth ")
				#screen.addstr("Mouse event \n")
				#screen.refresh()
				#boxList.refresh()
				if (my > 32 - J3Delta): 
			   		if ((mx > 0) and (mx < 10)):
				   		onNew()
			   		if ((mx > 10) and (mx < 20)):
				   		onNextDay()
			   		if ((mx > 20) and (mx < 30)):
				   		onNextSat()
			   		if (mx > 30):
				   		onSave()
	
				if ((my > 28 - J3Delta) and (my < 32 - J3Delta)):
			   		if ((mx > 0) and (mx < 10)):
				   		onDelete()
			   		if ((mx > 10) and (mx < 20)):
				   		onSearch()
			   		if ((mx > 20) and (mx < 30)):
				   		onPriMin()
			   		if (mx > 30):
				   		onScroll()

				if ((my >= firstRowListBox) and (my < 28 - J3Delta)):
					selectionIndex = offset + my - firstRowListBox
					tmpTodoItem = task_list[selectionIndex]
					#updateStatus("Mouse event at " + str(mx) + " - " + str(my) + tmpTodoItem.toString())
					updateDueDate()
					updateTask()

					#newItem = txtTask.edit()[0:-1].replace("\n", "-")
	
		   	
				#boxList.refresh()

			else:
				#screen.addstr("Other event \n")
				screen.refresh()
	#	screen.getch()
	
	finally:
		curses.endwin()
		



