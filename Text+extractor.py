
# coding: utf-8

# In[1]:

import re
import urllib
from bs4 import BeautifulSoup
import os


cwd = os.getcwd()
url = str(cwd).replace('C:','file://').replace('\\','/')+"/A330 Wheel.html"
html = urllib.request.urlopen(url)
soup = BeautifulSoup(html,"lxml")
soup.prettify(formatter=lambda s: s.replace("\xa0", ' '))
data = soup.findAll(text=True)

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title', 'html', '!DOCTYPE', 'meta']:
        return False
    elif re.match('<!--.*-->', str(element.encode('utf-8'))):
        return False
    #elif re.search("\xa0", element):
        #newtext = element.replace("\xa0", "")
        #element = element.replace(u'\xa0', u' ')
        #print(element)
        #element.replace_with(newtext)
    elif re.match('\n', element):
        return False
    return True
 
result = list(filter(visible, data))
##Replace all "/xa0" (nbsp-non-breaking space)
#if use for i in result => it is just a copy and will not modify the string
for i in range(len(result)):
    result[i] = result[i].replace("\xa0", " ")
#print (result)


# In[2]:

#use nltk to tokenize the content and check if it is a tool, consumable, workzone, or reference info
import nltk.data
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

from nltk.tokenize import word_tokenize


# ### Group text to sections according to the points

# In[3]:

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


# In[4]:

numSec = 0
taskIndicator = "TASK"
taskList = splitList(result,taskIndicator,0,len(taskIndicator))

#print(taskList[0])
#print(result[-1])


# In[5]:

allText = ' '.join([i.lower() for i in result])
allText


# In[6]:

fd = nltk.FreqDist(nltk.pos_tag(word_tokenize(allText)))
fd.most_common()
taggedItem = [(wt[0], wt[1],_) for (wt, _) in fd.most_common() if wt[1][0:2] == "NN"]
taggedItem


# In[7]:

taggedItem = [(wt[0], wt[1],_) for (wt, _) in fd.most_common() if wt[1][0:2] == "VB"]
taggedItem


# In[8]:

from nltk.tokenize import sent_tokenize
fd = nltk.FreqDist(nltk.pos_tag(word_tokenize(allText)))
fd.most_common()


# In[9]:

# get sub list from fromText to toText or end of main list
def getSubList(ls, fromText, toText):
    sub = []
    for i in range(len(ls)):
        if ls[i][0:len(fromText)] == fromText:
            while i < len(ls) and ls[i][0:len(toText)] != toText:
                sub.append(ls[i])
                i=i+1
            return sub    


# In[10]:

##Warning notices at the start of the task => use AR text to warn (##TODO: parse and beautify it)
Warning = getSubList(taskList[0],"WARNING","1")
#print(Warning)

##item1 = Reason for job (redundant for this case)
item1 = getSubList(taskList[0],"1","2")
#print(item1)

##item2 = Job setup info => Tools and equipments required for the job (can use AR to show the tools that need to be collected and verify **need images of tools)
item2 = getSubList(taskList[0],"2","3")
#print(item2)

##item3 = job set up (pre-job subtasks such as putting warning sign and deflating)
item3 = getSubList(taskList[0],"3","4")
#print(item3)

#item4 = Procedure (list of steps to complete task)
item4 = getSubList(taskList[0],"4","5")
#print(item4)
#print(taskList[0][-1])


# In[11]:

# parse item2 to get list of tools
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
#task->substask-> steps (action on object to object on params to paramsValue)


# In[12]:

toolsList= []
consumables = []
workzones = []
references = []


# In[13]:

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


# In[14]:

def isSerialNo(text):
    for i in nltk.pos_tag_sents(word_tokenize(text)):
        fd = nltk.FreqDist(i)
        taggedItem = [x for (wt, x) in fd.most_common() if wt[1] == 'CD']
        if sum(taggedItem)/len(i) >= 0.5 and len(i) > 1:
                return True
    return False


# In[15]:

word_t = word_tokenize(item2[31])
tag = nltk.pos_tag(word_t)
tag = nltk.pos_tag_sents(word_t)
fd = nltk.FreqDist(tag[1])
fd.most_common()
test = item2[65]
print(test)
isSerialNo(test)


# In[16]:

nltk.help.upenn_tagset('PDT')


# In[17]:

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


# In[18]:

toolsList, consumables, workzones, references = getSetupInfo(item2, ["A.","B.","C.","D."])
print("Tool list")
for t in toolsList:
    print (t.name, t.reference)
print("Consumables")
for c in consumables:
    print (c.name, c.reference)
print("Workzone")
for w in workzones:
    print (w.name, w.reference)    
print("References")
for r in references:
    print (r.name, r.reference) 


# In[19]:

# parse item3 to get subtasks to perform job (verification at the end of each subtask)
setUpSubTaskList = splitList(item3, "Subtask",0,len("Subtask"))
print(setUpSubTaskList)


# In[35]:

class subTask:
    steps = []
    def __init__(self, name, reference, ind, warning, parent):
        self.parent = parent
        self.name = name
        self.ind = ind
        self.warning = warning
        self.reference = reference
class step:
    target = []
    def __init__(self, description, action, component, tool, preTrackable, postTrackable, parent):
        self.parent = parent
        self.description = description
        self.action = action
        self.component = component
        self.tool = tool
        self.preTrackable =  preTrackable
        self.postTrackable = postTrackable
        
        
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


# In[21]:

suSubTaskList = []
st0 = subTask(setUpSubTaskList[0][2], word_tokenize(setUpSubTaskList[0][0])[1], 0, "", item3[1])


# In[22]:

numStep = 0
description = ""
descriptions = []
for i in setUpSubTaskList[0]:
    if i == '('+str(numStep+1)+')':
        if numStep > 0:
            descriptions.append(description)
        numStep += 1
        description = ""
    elif numStep > 0:
        description += i
descriptions.append(description)
        
nltk.pos_tag(word_tokenize(descriptions[0]))

toolListName = [t.name.lower()  for t in toolsList]
toolListName


# In[23]:

from nltk.corpus import wordnet
from collections import Counter

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


# In[24]:

#find tool in description
toolMatch, toolMatchIdx1 = matchTexts(descriptions[0],toolListName,2)        
toolMatch, toolMatchIdx1 


# In[25]:

#find nearest verb => action
#find nearest noun => component
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


# In[26]:

action, actionIdx = findNearestTag(descriptions[0],toolMatchIdx1,"VB")
com, componentIdx = findNearestTag(descriptions[0],toolMatchIdx1,"NN")
#Expand nNoun to contain neighbouring noun
#print (descriptions[0])
steps = []
steps.append(step(descriptions[0], action, com, toolMatch,"","",st0 ))
steps[0].parent.name


# In[27]:

ActionsListFile = open("Actions_List", 'r')
ActionsList = [i.replace('\n','') for i in ActionsListFile.readlines()]
#print (ActionsList)
ComponentsListFile = open("Components_List", 'r')
ComponentsList = [i.replace('\n','') for i in ComponentsListFile.readlines()]
#print (ComponentsList)


# In[28]:

#1. find tool 2. find component 3. first verb
def parseSubTaskList(setUpSubTaskList):
    suSubTaskList = []
    toolListName = [t.name  for t in toolsList]
    for i in range(len(setUpSubTaskList)):
        st = subTask(setUpSubTaskList[i][2], word_tokenize(setUpSubTaskList[i][0])[1], i, "", item3[1])
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
            sentences = re.split(r'[,.]', descriptions[k].lower())
            actions = []
            components = []
            tools = []
            for sent in sentences:
                action = ""
                component = ""
                tool = ""
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
            st.steps.append(step(descriptions[k], actions, components, tools,"","",st ))
    return suSubTaskList


# In[89]:

sttl = parseSubTaskList(setUpSubTaskList)


# In[90]:

x = 1
y = 1
print(sttl[x].steps[y].description.lower())
print(sttl[x].steps[y].action)
print(sttl[x].steps[y].component)
print(sttl[x].steps[y].tool)


# In[91]:

#1. Chunk the sentence
chunkSent = word_tokenize(sttl[x].steps[y].description)
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
print (result)


# In[92]:

# for every VP, check if there is an action and component or tool
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
            if leaf[0][0][0].lower() in sttl[x].steps[y].action: #contains action
                n = ' '.join([i[0] for i in leaf[1]])
                if sttl[x].steps[y].tool and re.search(sttl[x].steps[y].tool[0].replace('(S)',''),n): # contain tool (hack: to remove (S))
                    obj = n.replace(leaf[1][0][0],'')
                    objIsTool = True
                else:
                    for com in sttl[x].steps[y].component:
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
            if sttl[x].steps[y].tool and re.search(sttl[x].steps[y].tool[0].replace('(S)',''),n) and not objIsTool: # contain tool (hack: to remove (S))
                goal = n.replace(leaf[1][0][0],'')
                state = "in"
            else:
                for com in sttl[x].steps[y].component:
                    if re.search(com, n) and not objIsCom: #contain component
                        if objIsTool:
                            goal = n.replace(leaf[1][0][0],'')
                            state = "in"
                        else:
                            obj = n.replace(leaf[1][0][0],'')
                            objIsCom = True
print(unknown)
if objIsCom and goal == "":
    for leaf in result:
        if type(leaf) is nltk.Tree:
            if leaf.label() ==  'PST':
                state = leaf[0][0].lower()
                goal = leaf[1][0].lower()
        if not state and not goal and unknown:
            goal = unknown
            state = "has"
obj = obj[1:] if obj[0] == ' ' and obj else obj
state = state[1:] if state and state[0] == ' ' else state
goal = goal[1:] if goal and goal[0] == ' ' else goal
print (finalAction,obj,state,goal) 


# In[94]:

finalCom = component("","",{},"")
finalTool = tool("","",0,{},"")
if objIsTool:
    finalTool = [tool for tool in toolsList if tool.name.replace('(S)','').lower() == obj.lower()]
    finalTool = finalTool[0]
    if goal and state:
        finalTool.setAttribute(state+goal.upper(),False)
        comCand = [com for com in sttl[x].steps[y].component if re.search(goal.lower(), com)]
        if comCand:
            finalCom = component(comCand[0],"",{},"")
if objIsCom:
    finalCom = component(obj,"",{},"")
    if goal and state:
        finalCom.setAttribute(state+goal.upper(),False)

print (finalTool.attributes)
print (finalCom.attributes)

sttl[x].steps[y].action = finalAction if finalAction else sttl[x].steps[y].action[0]
sttl[x].steps[y].component = finalCom if finalCom else sttl[x].steps[y].component
sttl[x].steps[y].tool = finalTool if finalTool else sttl[x].steps[y].tool
print(sttl[x].steps[y].action)
print(sttl[x].steps[y].component.name)
print(sttl[x].steps[y].tool.name)


# In[134]:

print(result[0][0][0])


# In[44]:




# In[120]:




# In[121]:




# In[ ]:



