"""
The script is to replace English proper nouns with their  Chinese-origin proper nouns counterparts. The relationship between the two is the output of script "PropNounMapper.py" and it is stored in a file named "zhEnProperNounPairDict.txt". The script is to be used in the following way:
1. read the file "zhEnProperNounPairDict.txt" and store the relationship in a dictionary. the file format is "key:value", the key is chinese-origin proper noun and the value is its English counterpart. make the value to be key and the key to be value, so that the dictionary can be used to replace the English proper noun with its Chinese-origin counterpart.
2. read given equb file and replace the English proper noun with its Chinese-origin counterpart. At the middle of the process, it will record the count of replaced proper nouns in a dictionary. The key is the English proper noun and the value is the count of its replacement.
3. write the replaced equb file to a new file.
"""
import ebooklib # import the ebooklib library   
from ebooklib import epub # import the epub library

# read the file "zhEnProperNounPairDict.txt" and store the relationship in a dictionary. the file format is "key:value", the key is chinese-origin proper noun and the value is its English counterpart. make the value to be key and the key to be value, so that the dictionary can be used to replace the English proper noun with its Chinese-origin counterpart.
def readZhEnProperNounPairDict():
    zhEnProperNounPairDict = {}
    #read using utf-8 coding
    with open("zhEnProperNounPairDict.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                key, value = line.split(":")
                zhEnProperNounPairDict[value] = key
    return zhEnProperNounPairDict

# read given equb file and replace the English proper noun with its Chinese-origin counterpart. At the middle of the process, it will record the count of replaced proper nouns in a dictionary. The key is the English proper noun and the value is the count of its replacement.
def replaceEqub(zhEnProperNounPairDict, equbFile):
    properNounCountDict = {}
    book = epub.read_epub(equbFile)
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode('utf-8')
            for key in zhEnProperNounPairDict:
                if key in content:
                    count = content.count(key)
                    if key in properNounCountDict:
                        properNounCountDict[key] += count
                    else:
                        properNounCountDict[key] = count
                    content = content.replace(key, zhEnProperNounPairDict[key])
            item.set_content(content.encode('utf-8'))
    epub.write_epub("zh_" + equbFile, book)
    return properNounCountDict

# define the English equb file to be processed
equbFile = "10wYears-en.epub"

pairDict = readZhEnProperNounPairDict()

properNounCountDict = replaceEqub(pairDict, equbFile)
print(properNounCountDict)