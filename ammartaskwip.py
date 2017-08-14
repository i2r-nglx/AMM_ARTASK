##all required packages
import re
import urllib
from bs4 import BeautifulSoup
import os
import argparse
import nltk.data
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.corpus import wordnet
from collections import Counter
import pickle

##global variables
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')


##all classes
#TODO: Design and define trackable class
#tool class: contains the name, reference, quantity required for the task. attributes are set for target, trackable is used to identify the tool (will create the class in the future)
class tool:
	def __init__(self, name, reference, quantity, attributes, trackable):
		self.name = name
		self.quantity = quantity
		self.trackable = trackable
		self.attributes = attributes #a dictionary of attributes
		self.reference = reference
	def getAttribute(self, attribute_name):
		if attribute_name in self.attributes:
			return self.attributes[attribute_name]
		else:
			print(attribute_name+" is not an attribute of "+ self.name)
	def getAttributeList(self):
		return self.attributes.keys()
	def getName(self):
		return self.name
	def getTrackable(self):
		return self.trackable
	def setAttribute(self,attribute_name, newvalue):
			self.attributes[attribute_name] = newvalue
#consumable class: contains the name, reference and trackable          
class consumable:
	def __init__(self, name, reference, trackable):
		self.name = name
		self.trackable = trackable
		self.reference = reference
	def getName(self):
		return self.name
	def getTrackable(self):
		return self.trackable
	def setAttribute(self,attribute_name, newvalue):
		self.attributes[attribute_name] = newvalue
 #workzone class: contains the name, reference and trackable (may add location attributes such as coordinates or hangar no.)   
class workzone:
	def __init__(self, name, reference, trackable):
		self.name = name
		self.trackable = trackable
		self.reference = reference
	def getName(self):
		return self.name
	def getTrackable(self):
		return self.trackable
	def setAttribute(self,attribute_name, newvalue):
		self.attributes[attribute_name] = newvalue
#reference class: contains the name, reference and hyperlink 
class reference:
	def __init__(self, name, reference, hyperlink):
		self.name = name
		self.hyperlink = hyperlink
		self.reference = reference
	def getName(self):
		return self.name
	def getTrackable(self):
		return self.trackable
	def setAttribute(self,attribute_name, newvalue):
		self.attributes[attribute_name] = newvalue

#task class: root of each task 
class task:
	 #0:setup, 1:procedure, 2:clean up
	subTasks = []
	def __init__(self, name, reference, ind, warning):
		self.name = name
		self.ind = ind
		self.warning = warning
		self.reference = reference
#subtask class: contains the subtask, headed by 1. and A.
class subTask:
	steps = []
	def __init__(self, name, reference, ind, warning, parent):
		self.parent = parent
		self.name = name
		self.ind = ind
		self.warning = warning
		self.reference = reference
#step class: each step will have an action, component, tool and target based on a sentence of instruction. If sentence contains more than one group, then a substep will be appended to it automatically. headed by (1) and (a)
#preTrackable indicates start of step, postTrackable indicates end of step (derived from targeted attributes of tool/component)
class step:
	target = []
	subSteps = []
	def __init__(self, description, action, component, tool, preTrackable, postTrackable, parent):
		self.parent = parent
		self.description = description
		self.action = action
		self.component = component
		self.tool = tool
		self.preTrackable =  preTrackable
		self.postTrackable = postTrackable  
#component class: contains the name, reference, attributes and trackable (may add location in the future to the attributes)
class component:
	def __init__(self, name, reference, attributes, trackable):
		self.name = name
		#self.quantity = quantity
		self.trackable = trackable
		self.attributes = attributes #a dictionary of attributes
		self.reference = reference
	def getAttribute(self, attribute_name):
		if attribute_name in self.attributes:
			return self.attributes[attribute_name]
		else:
			print(attribute_name+" is not an attribute of "+ self.name)
	def getAttributeList(self):
		return self.attributes.keys()
	def getName(self):
		return self.name
	def getTrackable(self):
		return self.trackable
	def setAttribute(self,attribute_name, newvalue):
		self.attributes[attribute_name] = newvalue

#functions
#will be called in sequence
def visible(element):
	if element.parent.name in ['style', 'script', '[document]', 'head', 'title', 'html', '!DOCTYPE', 'meta']:
		return False
	elif re.match('<!--.*-->', str(element.encode('utf-8'))):
		return False
	elif re.match('\n', element):
		return False
	return True

def getAllTextFromHTML(filename):
	if re.match('C:',filename) or re.match('E:',filename):
		url = filename.replace('E:','file://').replace('C:','file://').replace('\\','/')
	elif re.match('http',filename):
		url = filename
	else:
		cwd = os.getcwd()
		url = str(cwd).replace('E:','file://').replace('C:','file://').replace('\\','/')+"/"+filename
		#url = filename

	print (url)
	html = urllib.request.urlopen(url)
	soup = BeautifulSoup(html,"lxml")
	soup.prettify(formatter=lambda s: s.replace("\xa0", ' '))
	data = soup.findAll(text=True)
	result = list(filter(visible, data))
	for i in range(len(result)):
		result[i] = result[i].replace("\xa0", " ")
	return result

def splitList(ls, text, startInd, numChar):
	subLs = []
	for i in range(len(ls)):
		if ls[i][startInd:numChar] == text:
			sub = []
			while i+1< len(ls) and ls[i+1][startInd:numChar] != text:
				sub.append(ls[i])
				i=i+1
				if i+1 == len(ls) or ls[i+1][startInd:numChar] == text: # last item in result
					sub.append(ls[i]) 
			subLs.append(sub)
	return subLs

def getSubList(ls, fromText, toText):
	sub = []
	for i in range(len(ls)):
		if ls[i][0:len(fromText)] == fromText:
			while i < len(ls) and ls[i][0:len(toText)] != toText:
				sub.append(ls[i])
				i=i+1
			return sub 

def getNumTag(text,tag):
	tokenized = word_tokenize(text)
	tagged = nltk.pos_tag(tokenized,tagset='universal')
	fd =  nltk.FreqDist(tagged)
	taggedItem = [wt[0] for (wt, _) in fd.most_common() if wt[1] == tag]
	return len(taggedItem)

def getTagged(text):
	tokenized = word_tokenize(text)
	tagged = nltk.pos_tag(tokenized,tagset='universal')
	fd =  nltk.FreqDist(tagged)
	return fd.most_common()

def isSerialNo(text):
	for i in nltk.pos_tag_sents(word_tokenize(text)):
		fd = nltk.FreqDist(i)
		taggedItem = [x for (wt, x) in fd.most_common() if wt[1] == 'CD']
		if sum(taggedItem)/len(i) >= 0.5 and len(i) > 1:
				return True
	return False

def getSetupInfo(section, subheading):
	toolList = []
	consumableList = []
	workzoneList = []
	referenceList = []
	currSection = ""
	sectionID = 0;
	for i in range(len(section)):
		if section[i] == subheading[sectionID]:
			currSection = subheading[sectionID]
			sectionID = (sectionID+1)%len(subheading)
		#condition contains noun, i-1 contain 1 noun or num, i-2 contain 1 noun or num and has than 3 char (not optimal)
		if currSection == subheading[0] and getNumTag(section[i],"NOUN") > 0 and len(word_tokenize(section[i-1])) == 1 and (getNumTag(section[i-1],"NOUN") == 1 or getNumTag(section[i-1],"NUM") == 1) and len(word_tokenize(section[i-2])) >= 2 and (getNumTag(section[i-2],"NOUN") == 1 or getNumTag(section[i-2],"NUM") == 1):
			toolList.append(tool(section[i],section[i-2],section[i-1],{},""))
		if currSection == subheading[1] and getNumTag(section[i],"NOUN") > 0 and len(word_tokenize(section[i-1])) == 1 and getNumTag(section[i-1],".") == 1 and len(word_tokenize(section[i-2])) == 1 and (getNumTag(section[i-2],"NOUN") == 1 or getNumTag(section[i-2],"NUM") == 1):
			consumableList.append(consumable(section[i],section[i-2],""))
		if currSection == subheading[2] and getNumTag(section[i],"NOUN") >= 2 and len(word_tokenize(section[i-1])) == 1 and getNumTag(section[i-1],"NUM") == 1:
			workzoneList.append(workzone(section[i],section[i-1],""))
		if currSection == subheading[3] and getNumTag(section[i],"NOUN") >= 2 and len(word_tokenize(section[i-1])) > 0 and "Ref" in section[i-1]:
			referenceList.append(reference(section[i],section[i-1],""))
		elif currSection == subheading[3] and getNumTag(section[i],"NOUN") >= 4:
			referenceList.append(reference(section[i],"NA",""))
	return toolList, consumableList, workzoneList, referenceList

def matchTexts(list1, list2, numMatch):
	matchIdx = []
	for idx1, word1 in enumerate(word_tokenize(list1)):
		for idx2, t in enumerate(list2):
			list3 = word_tokenize(t)
			for word2 in list3:
				#print(word2)
				wordFromList1 = wordnet.synsets(word1)
				wordFromList2 = wordnet.synsets(word2)
				if wordFromList1 and wordFromList2:
					s = wordFromList1[0].wup_similarity(wordFromList2[0])
					if not s:
						s = 0.0
					if s > 0.8:
						matchIdx.append((idx1,idx2))
	x = Counter([y for (x,y) in matchIdx]).most_common(1)
	idx = [i for (i,j) in matchIdx if j == x[0][0]]
	#print(len(idx), len(word_tokenize(list2[x[0][0]])))
	if x and x[0][1] >= numMatch and len(idx)/len(word_tokenize(list2[x[0][0]])) > 0.5:
		return list2[x[0][0]], idx
	else:
		return "None",[]

def findNearestTag(textToSearch, matchIdx, tag):
	token = word_tokenize(textToSearch)
	tagged = (nltk.pos_tag(token))
	for i in range(len(token)):
		#search forward
		if i+matchIdx[0] not in matchIdx and i+matchIdx[0] < len(token):
			if tagged[i+matchIdx[0]][1][0:2] == tag:
				return (tagged[i+matchIdx[0]][0]), i+matchIdx[0]
		#search backword
		if matchIdx[0]-i not in matchIdx and matchIdx[0]-i >= 0:
			if tagged[matchIdx[0]-i][1][0:2] == tag:
				return (tagged[matchIdx[0]-i][0]), matchIdx[0]-i
	return "",-1       

def parseSubTaskList(setUpSubTaskList, toolListName, item, ActionsList, ComponentsList):
	suSubTaskList = []
	#toolListName = [t.name  for t in toolsList]
	for i in range(len(setUpSubTaskList)):
		st = subTask(setUpSubTaskList[i][2], word_tokenize(setUpSubTaskList[i][0])[1], i, "", item[1])
		## hack to remove warning
		if re.search("DECREASE",setUpSubTaskList[i][2]):
			st = subTask(setUpSubTaskList[i][4], word_tokenize(setUpSubTaskList[i][0])[1], i, "", item[1])
		suSubTaskList.append(st)
		st.steps=[]
		numStep = 0
		description = ""
		descriptions = []
		for j in setUpSubTaskList[i]:
			if j == '('+str(numStep+1)+')':
				if numStep > 0:
					descriptions.append(description)
				numStep += 1
				description = ""
			elif numStep > 0:
				description += j
		descriptions.append(description)
		if not descriptions[0]:
			descriptions[0] = setUpSubTaskList[i][2]
		for k in range(len(descriptions)):
			#sentences = re.split(r'[.]', descriptions[k].lower())
			sentences = sent_tokenize(descriptions[k].lower())

			for sent in sentences:
				actions = []
				components = []
				tools = []
				action = ""
				component = ""
				tool = ""
				if len(sent) > 1 and not (sent[0] == 'a' and sent[1] == 'm'):
					toolMatch, toolMatchIdx = matchTexts(sent.lower(),toolListName,2)
					actionMatch, actionIdx = matchTexts(sent.lower(),ActionsList,1)
					componentMatch, componentIdx = matchTexts(sent.lower(),ComponentsList,1)
					if (not toolMatch == "None") and actionMatch == "None":
						actionMatch, actionIdx = findNearestTag(sent,[toolMatchIdx[0]],"VB")
					if (not toolMatch == "None") and componentMatch == "None":
						componentMatch, componentIdx = findNearestTag(sent,[toolMatchIdx[0]],"NN")    
					if not actionMatch == "None":
						action = actionMatch
						actions.append(action)
					if not componentMatch == "None":
						component = componentMatch
						components.append(component)
					if not toolMatch == "None":
						tool = toolMatch
						tools.append(tool)
				if actions or components or tools:
					st.steps.append(step(sent, actions, components, tools,"","",st ))
	return suSubTaskList

def parseStepForTarget(step, toolsList):
	chunkSent = word_tokenize(step.description)
	#chunckSent = [nltk.word_tokenize(sent) for sent in chunckSent]
	chunkSent = nltk.pos_tag(chunkSent)
	grammar = r"""
	NP: {<DT>?<JJ>*<NN|NNP|NNS>+} 
	ACT: {<VB|PDT>}
	PST: {<VBZ><VBN>}
	VP: {<ACT>+<NP>}
	TNP: {<TO><NP>} 
	INP: {<IN><NP>}
	"""
	cp = nltk.RegexpParser(grammar)
	result = cp.parse(chunkSent)
	target=[]
	#object to act on
	obj = ""
	#goal of the object
	goal = ""
	#end state (in, to, attributes)
	state = ""
	finalAction = ""
	unknown = ""
	objIsTool = False
	objIsCom = False
	hasAction = False
	for leaf in result:
		if type(leaf) is nltk.Tree:
			if leaf.label() ==  'VP':
				if leaf[0][0][0].lower() in step.action: #contains action
					n = ' '.join([i[0] for i in leaf[1]])
					if step.tool and re.search(step.tool[0].replace('(S)',''),n): # contain tool (hack: to remove (S))
						obj = n.replace(leaf[1][0][0],'')
						objIsTool = True
					else:
						for com in step.component:
							if re.search(com, n): #contain component
								obj = n.replace(leaf[1][0][0],'')
								objIsCom = True
						if not objIsCom:
							obj = n.replace(leaf[1][0][0],'')
					finalAction = leaf[0][0][0].lower()
					if not objIsTool and not objIsCom:
						unknown = n.replace(leaf[1][0][0],'')
			if leaf.label() == 'INP':
				n = ' '.join([i[0] for i in leaf[1]])
				if step.tool and re.search(step.tool[0].replace('(S)',''),n) and not objIsTool: # contain tool (hack: to remove (S))
					goal = n.replace(leaf[1][0][0],'')
					state = "in"
				else:
					for com in step.component:
						if re.search(com, n) and not objIsCom: #contain component
							if objIsTool:
								goal = n.replace(leaf[1][0][0],'')
								state = "in"
							else:
								obj = n.replace(leaf[1][0][0],'')
								objIsCom = True
	if objIsCom and goal == "":
		for leaf in result:
			if type(leaf) is nltk.Tree:
				if leaf.label() ==  'PST':
					state = leaf[0][0].lower()
					goal = leaf[1][0].lower()
			if not state and not goal and unknown:
				goal = unknown
				state = "has"
	obj = obj[1:] if obj and obj[0] == ' ' else obj
	state = state[1:] if state and state[0] == ' ' else state
	goal = goal[1:] if goal and goal[0] == ' ' else goal   
	finalCom = component("","",{},"")
	finalTool = tool("","",0,{},"")
	if objIsTool:
		finalTool = [tool for tool in toolsList if tool.name.replace('(S)','').lower() == obj.lower()]
		finalTool = finalTool[0]
		if goal and state:
			finalTool.setAttribute(state+goal.upper(),False)
			comCand = [com for com in step.component if re.search(goal.lower(), com)]
			if comCand:
				finalCom = component(comCand[0],"",{},"")
	if objIsCom:
		finalCom = component(obj,"",{},"")
		if goal and state:
			finalCom.setAttribute(state+goal.upper(),False)  
	step.action = finalAction if finalAction else step.action
	if type(step.action) == list:
		if step.action:
			step.action = step.action[0]
		else:
			step.action = ""
	step.component = finalCom if not finalCom.name == "" else step.component
	step.tool = finalTool if not finalTool.name =="" else step.tool 
	if type(step.component) == list:
		if step.component:
			step.component = component(step.component[0],"",{},"")
		else:
			step.component = component("","",{},"")
	if type(step.tool) == list:
		if step.tool:
			step.tool = tool(step.tool[0],"",0,{},"")
		else:
			step.tool = tool("","",0,{},"")

def main():
	filename = "A330 Wheel.htm"
	output = "amm-artask.txt"
	indtask = False
	parser = argparse.ArgumentParser(description='Take in a AMM html file and extract the info to an ARTASK model')
	parser.add_argument('-f','--filename', type=str, nargs = 1,
					   help='Filename of AMM html')
	parser.add_argument('-o', '--output', type=str, nargs = 1,
					   help='Filename of output')
	parser.add_argument('-t', '--indtask', dest='indtask', action='store_true',
					   help='Print task individually')

	opts = parser.parse_args()

	if opts.filename:
		filename = opts.filename[0]
		#print(filename)
	if opts.output:
		output = opts.output[0]
		#print(output)
	if opts.indtask:
		indtask = True
	#print(indtask)
	getTasks(filename,output,indtask)

def getTasks(filename,output,create_individual_task_output):
	result = getAllTextFromHTML(filename)                 
	taskIndicator = "TASK"
	taskList = splitList(result,taskIndicator,0,len(taskIndicator))
	tasks = []

	for i in range(len(taskList)):
		##Warning notices at the start of the task => use AR text to warn (##TODO: parse and beautify it)
		warningMsg = getSubList(taskList[i],"WARNING","1")
		#print(Warning)

		items = []
		subTasks = []


		for j in range(1,6):
			if j == 2:
				item = getSubList(taskList[i],str(j),str(j+1)+'.')
			elif j+1==2:
				item = getSubList(taskList[i],str(j)+'.',str(j+1))
			else:
				item = getSubList(taskList[i],str(j)+'.',str(j+1)+'.')
			items.append(item)

		##item1 = Reason for job (redundant for this case)
		item1 = getSubList(taskList[i],"1","2")
		#print(item1)

		##item2 = Job setup info => Tools and equipments required for the job (can use AR to show the tools that need to be collected and verify **need images of tools)
		item2 = getSubList(taskList[i],"2","3")
		#print(item2)

		##item3 = job set up (pre-job subtasks such as putting warning sign and deflating)
		item3 = getSubList(taskList[i],"3","4")
		#print(item3)

		#item4 = Procedure (list of steps to complete task)
		item4 = getSubList(taskList[i],"4","5")

		#item4 = Clean up (list of steps to complete task)
		item5 = getSubList(taskList[i],"5","6")

		toolsList= []
		consumables = []
		workzones = []
		references = []

		toolsList, consumables, workzones, references = getSetupInfo(items[1], ["A.","B.","C.","D."])
		toolListName = [t.name  for t in toolsList]
		#print (toolListName)
		ActionsListFile = open("Actions_List", 'r')
		ActionsList = [a.replace('\n','') for a in ActionsListFile.readlines()]
		#print (ActionsList)
		ComponentsListFile = open("Components_List", 'r')
		ComponentsList = [c.replace('\n','') for c in ComponentsListFile.readlines()]

		for k in range(2,5):
			if items[k]:
				setUpSubTaskList = splitList(items[k], "Subtask",0,len("Subtask"))
				sttl = parseSubTaskList(setUpSubTaskList, toolListName, items[k], ActionsList, ComponentsList)
				for st in sttl:
					for step in st.steps:
						parseStepForTarget(step, toolsList)
				subTasks.append(sttl)
		tsk = task(taskList[i][1], taskList[i][0][5:],i,warningMsg)
		tsk.subTasks = subTasks
		tasks.append(tsk)

	if create_individual_task_output:
		for t in tasks:
			output = t.name + ".txt"
			f = open(output,'w')        
			print(t.name, file = f)
			print(t.reference, file = f)
			print(t.warning,file = f)
			for sst in t.subTasks:
				for st in sst:
					print(' '+st.name, file = f)
					print(' '+st.reference, file = f)
					for stp in st.steps:
						print('  '+stp.description,file=f)
						print('  A: '+stp.action,file=f)
						print('  C: '+stp.component.name,file=f)
						for key in stp.component.attributes:
							print ('   '+key, ":", stp.component.attributes[key], file = f)
						print('  T: '+stp.tool.name,file=f)
						for key in stp.tool.attributes:
							print ('   '+key, ":", stp.tool.attributes[key], file = f)
			f.close()
	else:
		f = open(output,'w')
		for t in tasks:        
			print(t.name, file = f)
			print(t.reference, file = f)
			print(t.warning,file = f)
			for sst in t.subTasks:
				for st in sst:
					print(' '+st.name, file = f)
					print(' '+st.reference, file = f)
					for stp in st.steps:
						print('  '+stp.description,file=f)
						print('  A: '+stp.action,file=f)
						print('  C: '+stp.component.name,file=f)
						for key in stp.component.attributes:
							print ('   '+key, ":", stp.component.attributes[key], file = f)
						print('  T: '+stp.tool.name,file=f)
						for key in stp.tool.attributes:
							print ('   '+key, ":", stp.tool.attributes[key], file = f)
		f.close()

	return tasks
if __name__ == '__main__':
	main()