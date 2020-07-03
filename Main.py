from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
from networkx.drawing.nx_agraph import graphviz_layout
from nltk.stem import SnowballStemmer
from os import listdir
import networkx as nx
import matplotlib.pyplot as plt
import io

def ParsePDFsFromDir(dir):
    """
    this function parses all the pdf files in a given directory.
    """
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    files = [f for f in listdir(dir)]
    pdfFiles = []
    yearOfFile = []
    for file in files:
        print("parsing "+file)
        for i in range(0,len(file)):
            if file[i] == '2':
                yearOfFile.append(file[i]+file[i+1]+file[i+2]+file[i+3])
        with open(dir+"/"+file, 'rb') as fh:
            for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
                page_interpreter.process_page(page)
            text = fake_file_handle.getvalue()
            fake_file_handle.truncate(0)
            fake_file_handle.seek(0)
        text = text.replace('-',' ')
        text = text.replace('’',' ')
        lines = text.splitlines(False)
        curr = []
        for l in lines:
            curr.append(l.split())
        pdfFiles.append(curr)
    converter.close()
    fake_file_handle.close()
    return (pdfFiles,yearOfFile)
def PArseTXTFromDir(dir):
    """
    this function parses all the TXT files in a directory.
    """
    files = [f for f in listdir(dir)]
    pdfFiles = []
    yearOfFile = []
    for file in files:
        print("parsing "+file)
        for i in range(0, len(file)):
            if file[i] == '2' and file[i+1] == '0':
                yearOfFile.append(file[i] + file[i + 1] + file[i + 2] + file[i + 3])
        with open(dir + "/" + file, 'r') as fh:
            lines = fh.readlines()
        lines = [line[:-1] for line in lines]
        lines = [line.replace('-',' ') for line in lines]
        lines = [line.replace('’',' ') for line in lines]
        curr = [line.split() for line in lines]
        pdfFiles.append(curr)
    return (pdfFiles, yearOfFile)
def ParseTXTFile(file):
    """
    this function reads a txt file given its name.
    """
    with open(file,'r') as txt:
        ignoreList = txt.readlines()
    ignoreList = [line[:-1] for line in ignoreList]
    return ignoreList

def cleanFiles(pdfFiles,ignoreList):
    """
    this function returns a list of lines of words including only the wanted words.
    """
    newPdfFiles = []
    for file in pdfFiles:
        curr = []
        for line in file:
            lineWords = []
            for word in line:
                word = word.lower()
                if len(word) == 1 or not word.isalpha() or word in ignoreList:
                    continue
                lineWords.append(word)
            if len(lineWords) != 0:
                curr.append(lineWords)
        newPdfFiles.append(curr)
    return newPdfFiles

def getFreq(pdfFiles):
    """
    this function calculates the frequency of each word.
    """
    freq = {}
    for file in pdfFiles:
        for line in file:
            for word in line:
                if word in freq:
                    freq[word] += 1
                else:
                    freq[word] = 1
    return freq
def makeWordsTxt(freq):
    """
    this function creates a txt file that contains all the words sorted along with each words frequency.
    """
    temp = []
    for word in freq:
        temp.append((word,freq[word]))
    temp.sort()
    with open('words.txt','w') as out:
        for i in temp:
            out.write(str(i[0])+" "+str(i[1])+"\n")

def getFreqPerFile(pdfFiles):
    """
    this function calculates the frequency of each word within each file.
    """
    freq = []
    for file in pdfFiles:
        curr = {}
        for line in file:
            for word in line:
                if word in curr:
                    curr[word] += 1
                else:
                    curr[word] = 1
        freq.append(curr)
    return freq

def stemmatiztion(tokens):
    ps = SnowballStemmer(language='english')
    return list(map(ps.stem,tokens))

temp = PArseTXTFromDir("pdftotext")
pdfFiles = temp[0]
yearOfFile = temp[1]
pdfFiles = cleanFiles(pdfFiles,ParseTXTFile("ignoreList.txt"))
pdfFiles = [[stemmatiztion(line) for line in file] for file in pdfFiles]
freq = getFreq(pdfFiles)
pdfFiles = [[[word for word in line if freq[word]>5] for line in file] for file in pdfFiles]
freq = dict((word,value) for word, value in freq.items() if freq[word]>5)
print(len(freq))
quit(0)
makeWordsTxt(freq)
freqPerFile = getFreqPerFile(pdfFiles)

G = nx.Graph()
#the colors used in the graph.
colors = ['#202970','#2E61A5','#4893CF','#48958F','#48914E','#94B945','#F0E855','#DC973A','#C63127','#C52C4F']
mp = {}
cnt = 0
for i in range(2008,2018):
    mp[i] = cnt
    cnt += 1

nodeColors = []
nodeSizes = []
for word in freq:
    id = 0
    for i in range(0,len(pdfFiles)):
        if word in freqPerFile[i] and word in freqPerFile[id] and \
                freqPerFile[i][word]>=freqPerFile[id][word]:
            id = i
    G.add_node(word)
    nodeColors.append(colors[mp[int(yearOfFile[id])]])
    nodeSizes.append(freq[word])

# change 20 to a different number to scale all the nodes' sizes
for i in range(0,len(nodeSizes)):
    nodeSizes[i] *= 20


print("creating graph")
# initializing the list edgeConnection that contains the strength of the connection between any two nodes
edgeConnection = []
for i in range(0, len(pdfFiles)):
    edgeConnection.append({})
    for word1 in freq:
        edgeConnection[i][word1] = {}
        for word2 in freq:
            edgeConnection[i][word1][word2] = 0

for i in range(0,len(pdfFiles)):
    for line in pdfFiles[i]:
        for word1 in line:
            for word2 in line:
                if word1 != word2:
                    if not G.has_edge(word1,word2):
                        G.add_edge(word1,word2,weight = 1)
                        edgeConnection[i][word1][word2] = 1
                        edgeConnection[i][word2][word1] = 1
                    else:
                        G[word1][word2]['weight'] += 1
                        edgeConnection[i][word1][word2] += 1
                        edgeConnection[i][word2][word1] += 1

# chooses the color of the edge based on it's connection strength
for word1 in freq:
    for word2 in freq:
        if G.has_edge(word1,word2):
            id = 0
            for i in range(0,len(pdfFiles)):
                if edgeConnection[i][word1][word2] >= edgeConnection[id][word1][word2]:
                    id = i
            G[word1][word2]['color'] = colors[mp[int(yearOfFile[id])]]


edgeColors = [G[u][v]['color'] for u,v in G.edges]
weights = [G[u][v]['weight']*0.1 for u,v in G.edges]
for edge in G.edges:
  if G[edge[0]][edge[1]]['weight'] <= 5:
    G.remove_edge(edge[0],edge[1])

print(G.number_of_edges())
print(G.number_of_nodes())
print("drawing")
plt.figure(1,figsize=(30,30))
#the following commands contols the drawing of the graph, you can change the layout to any different one.
nx.draw(G,pos = nx.nx_pydot.graphviz_layout(G,'fdp'),with_labels = True,width = weights, node_size = nodeSizes, node_color = nodeColors, edge_color = edgeColors)
plt.savefig("visualization.png")
