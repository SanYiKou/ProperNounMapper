"""
This script is to convert the proper nouns in the English translated novel back to their original Chinese forms.

Overview:
use an NER model in NLP for both Chinese and English files to extract their proper nouns. Then, we can use the Chinese Pinyin system to translate Chinese proper nouns into their Pinyin format. The next step is to employ fuzzy matching technology to match Chinese proper nouns in Pinyin format with their English counterparts. This will enable us to connect Chinese-origin proper nouns with their English counterparts.
"""
import json
import ebooklib # import the ebooklib library   
from ebooklib import epub # import the epub library
from bs4 import BeautifulSoup # import the BeautifulSoup library
import spacy  # import the spacy library
import threading
# import a library to do fuzzy matching
from fuzzywuzzy import fuzz

# import a library can be used to convert Chinese characters to Pinyin
from pypinyin import pinyin, lazy_pinyin, Style

# set a limit to the number of chapters to be processed. this is to avoid processing the entire novel, which will take a long time.
chapterLimit = 9999
# Config max number of threads to use.
maxThreads = 20

enNlp = spacy.load("en_core_web_lg") # load the English model
cnNlp = spacy.load("zh_core_web_lg") # load the Chinese model

# encapsulate the above code in a function. the function is to get the content dictionary of a novel.
def getContentDict(book):
    docs = book.get_items_of_type(ebooklib.ITEM_DOCUMENT) # get a list of document items
    contentDict = {} # create a dictionary to store the novel content
    
    global chapterLimit

    limit = chapterLimit

    for doc in docs: # iterate over document items

        # check if the chapter limit is reached
        if limit == 0: break
        limit -= 1

        content = doc.get_content().decode('utf-8') # get HTML content as a string

        soup = BeautifulSoup(content, 'html.parser') # parse HTML using BeautifulSoup

        # find chapter title content at heading tag in body tag, support multiple heading tag, such as h1, h2, h3, etc.
        title = soup.find('body').find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        if title == None : continue
        title = title.get_text()
        # print(title)

        # collect each paragraph in the chapter into a list
        paras = []
        for p in soup.find_all('p'):
            paras.append(p.get_text().replace('\u3000',''))

        # make a dictionary of chapter title and paragraph list
        chapter = {title: paras}
        # add the chapter dictionary to the novel dictionary
        contentDict.update(chapter)

    return contentDict

# encapsulate the above code in a function. the function is to get ProperNounDict of specific language.
def getProperNounDict(contentDict, nlp):
    properNounDict = {} # create a dictionary to store the proper nouns

    # use a variable to record the remaining number of chapters in the novel and will be used to record the progress of the script
    chapterCount = len(contentDict)

    for chapter in contentDict: # iterate over each chapter in the novel
        # record progress
        chapterCount -= 1
        print("Remaining chapters: " + str(chapterCount))

        # iterate each paragraph in the chapter
        for para in contentDict[chapter]:
            # create a doc object from the paragraph
            doc = nlp(para)
            # iterate over each token in the doc
            for token in doc:
                # if is successive PROPN, join it together with previous PROPN, and continue to next iteration, otherwise, add it to the proper noun dictionary
               
                # check if the token is a proper noun
                if token.pos_ == "PROPN":
                    # check if the token is a successive proper noun
                    if token.i > 0 and doc[token.i - 1].pos_ == "PROPN":
                        # if the token is a successive proper noun, join it together with the previous proper noun
                        properNoun = doc[token.i - 1].text + " " + token.text
                    else:
                        # if the token is not a successive proper noun, add it to the proper noun dictionary
                        properNoun = token.text

                    # check if the proper noun is in the proper noun dictionary
                    if properNoun in properNounDict:
                        # if the proper noun is in the proper noun dictionary, increment the count by 1
                        properNounDict[properNoun] += 1
                    else:
                        # if the proper noun is not in the proper noun dictionary, add the proper noun to the proper noun dictionary with a count of 1
                        properNounDict[properNoun] = 1
    
    # sort the proper noun dictionary by the count in descending order
    properNounDict = dict(sorted(properNounDict.items(), key=lambda item: item[1], reverse=True))

    return properNounDict


# rewrite getProperNounDict into a parallel version to use multiple threading to speed up the process. we can parallel process every chapter in the novel. 

def getProperNounDictParallel(contentDict, nlp):
    properNounDict = {} # create a dictionary to store the proper nouns

    # use a variable to record the remaining number of chapters in the novel and will be used to record the progress of the script
    chapterCount = len(contentDict)

    # create a list to store the threads
    threads = []

   
    global maxThreads

    # iterate over each chapter in the novel
    for chapter in contentDict:
        # record progress
        chapterCount -= 1
        print("Remaining chapters: " + str(chapterCount))

        # create a thread to process the chapter
        t = threading.Thread(target=processChapter, args=(contentDict[chapter], nlp, properNounDict))
        threads.append(t)
        t.start()

        # check if the number of threads is greater than the max number of threads
        if len(threads) >= maxThreads:
            # wait for the first thread to finish
            threads[0].join()
            # remove the first thread from the list
            threads.pop(0)
    
    # wait for all threads to finish
    for thread in threads:
        thread.join()

    # sort the proper noun dictionary by the count in descending order
    properNounDict = dict(sorted(properNounDict.items(), key=lambda item: item[1], reverse=True))

    return properNounDict

# processChapter is a function to process a chapter in the novel
def processChapter(chapter, nlp, properNounDict):
    # iterate each paragraph in the chapter
    for para in chapter:
        # create a doc object from the paragraph
        doc = nlp(para)
        # iterate over each token in the doc
        for token in doc:
            # if is successive PROPN, join it together with previous PROPN, and continue to next iteration, otherwise, add it to the proper noun dictionary
           
            # check if the token is a proper noun
            if token.pos_ == "PROPN":
                # check if the token is a successive proper noun
                if token.i > 0 and doc[token.i - 1].pos_ == "PROPN":
                    # if the token is a successive proper noun, join it together with the previous proper noun
                    properNoun = doc[token.i - 1].text + " " + token.text
                else:
                    # if the token is not a successive proper noun, add it to the proper noun dictionary
                    properNoun = token.text

                # check if the proper noun is in the proper noun dictionary
                if properNoun in properNounDict:
                    # if the proper noun is in the proper noun dictionary, increment the count by 1
                    properNounDict[properNoun] += 1
                else:
                    # if the proper noun is not in the proper noun dictionary, add the proper noun to the proper noun dictionary with a count of 1
                    properNounDict[properNoun] = 1



  
    


# load the origin Chinese epub file
book = epub.read_epub('wudaozongshi.epub')

# get the content dictionary of the Chinese novel
zhContentDict = getContentDict(book)

zhProperNounDict = getProperNounDictParallel(zhContentDict, cnNlp) # get the proper noun dictionary of the Chinese novel



# convert the Chinese proper nouns to their Pinyin format
zhProperNounPinyinDict = {} # create a dictionary to store the Chinese proper nouns in Pinyin format. the key is the Pinyin format, and the value is the key value pair of the count and a list of proper nouns


# use a variable to record the remaining number of proper nouns in the Chinese proper noun dictionary and will be used to record the progress of the script
properNounCount = len(zhProperNounDict)

for properNoun in zhProperNounDict: # iterate over each proper noun in the Chinese proper noun dictionary
    # record progress
    properNounCount -= 1
    print("Remaining proper nouns: " + str(properNounCount))

    # convert the proper noun to its Pinyin format
    pinyin = lazy_pinyin(properNoun)

    # convert the Pinyin format to a string
    pinyin = ''.join(pinyin)

    # check if the Pinyin format is in the Pinyin dictionary
    if pinyin in zhProperNounPinyinDict:
        # if the Pinyin format is in the Pinyin dictionary, add the proper noun to the list of proper nouns
        zhProperNounPinyinDict[pinyin][1].append(properNoun)
    else:
        # if the Pinyin format is not in the Pinyin dictionary, add the Pinyin format to the Pinyin dictionary with a count of 1 and a list of proper nouns
        zhProperNounPinyinDict[pinyin] = [zhProperNounDict[properNoun], [properNoun]]

# remove item from the Pinyin dictionary if the count of the proper noun is less than 10
for pinyin in list(zhProperNounPinyinDict):
    if zhProperNounPinyinDict[pinyin][0] < 10:
        zhProperNounPinyinDict.pop(pinyin)

# print the proper noun Pinyin dictionary
print(zhProperNounPinyinDict)


# load the English translated epub file
book = epub.read_epub('wudaozongshi-en.epub')


# get the content dictionary of the English translated novel
enContentDict = getContentDict(book)

enProperNounDict = getProperNounDictParallel(enContentDict, enNlp) # get the proper noun dictionary of the English translated novel

# remove item from the English proper noun dictionary if the count of the proper noun is less than 10
for properNoun in list(enProperNounDict):
    if enProperNounDict[properNoun] < 10:
        enProperNounDict.pop(properNoun)

# print the proper noun dictionary
print(enProperNounDict)

# Fuzz match pinyin which is the key of zhProperNounPinyinDict with English proper noun, and store the result in a dictionary.
zhEnProperNounDict = {} # create a dictionary to store the result of the Fuzz match


# use a variable to record the remaining number of Pinyin in the Chinese proper noun Pinyin dictionary and will be used to record the progress of the script
pinyinCount = len(zhProperNounPinyinDict)

for pinyin in zhProperNounPinyinDict: # iterate over each Pinyin in the Chinese proper noun Pinyin dictionary
    # record progress
    pinyinCount -= 1
    # print("Remaining Pinyin: " + str(pinyinCount))

    # iterate over each proper noun in the list of proper nouns
    for properNoun in zhProperNounPinyinDict[pinyin][1]:
        # iterate over each English proper noun
        for enProperNoun in enProperNounDict:
            # fuzz match pinyin with lowered enProperNoun
            ratio = fuzz.ratio(pinyin, enProperNoun.lower().replace(" ", ""))

            # store the match and score to the result dictionary if score is greater than 80
            if ratio > 90:
                # check if the Chinese proper noun is in the result dictionary
                if properNoun in zhEnProperNounDict:
                    # if the Chinese proper noun is in the result dictionary, add the English proper noun and score to the list
                    zhEnProperNounDict[properNoun].append([enProperNoun, ratio])
                else:
                    # if the Chinese proper noun is not in the result dictionary, add the Chinese proper noun to the result dictionary with a list of English proper noun and score
                    zhEnProperNounDict[properNoun] = [[enProperNoun, ratio]]

# for the result dictionary, keep the one with the highest score
for properNoun in zhEnProperNounDict:
    # sort the list of English proper noun and score by the score in descending order
    zhEnProperNounDict[properNoun] = sorted(zhEnProperNounDict[properNoun], key=lambda item: item[1], reverse=True)

    # keep the one with the highest score
    zhEnProperNounDict[properNoun] = zhEnProperNounDict[properNoun][0]

# sort the result dictionary by the score in descending order
zhEnProperNounDict = sorted(zhEnProperNounDict.items(), key=lambda item: item[1][1], reverse=True)

# remove zh proper noun with length of 1
zhEnProperNounDict = [item for item in zhEnProperNounDict if len(item[0]) > 1] 

# print the result dictionary
print(zhEnProperNounDict)

# remove en proper noun which has upper letter length of 1
zhEnProperNounDict = [item for item in zhEnProperNounDict if len([c for c in item[1][0] if c.isupper()]) > 1]


# save the result dictionary to a readable json file.
with open('zhEnProperNounDict.json', 'w', encoding='utf-8') as f:
    json.dump(zhEnProperNounDict, f, ensure_ascii=False, indent=4)



# create a pair dictionary, the key is zh proper noun, the value is en proper noun
zhEnProperNounPairDict = {item[0]: item[1][0] for item in zhEnProperNounDict}

# save the pair dictionary to a text file with encoding of utf-8, the format is "key:value"
with open('zhEnProperNounPairDict.txt', 'w', encoding='utf-8') as f:
    for key, value in zhEnProperNounPairDict.items():
        f.write("%s:%s\n" % (key, value)) 
