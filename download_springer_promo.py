# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 18:05:45 2020

@author: Miguel
"""

# =============================================================================
#%%   Get Doi (url) to all the books in the message
# =============================================================================
import json
from selenium.common.exceptions import WebDriverException
import inspect
from copy import deepcopy
from dask.rewrite import _match

with open('free_springer_dois', 'r', encoding='utf8', errors='ignore') as f:
    data = f.read()

books = {}

data = data.split('\n')
info = [ str_.split('\t') for str_ in data]

books_by_subject = {}

for i, string_ in enumerate(info):    
    title, subject, doi = string_
    books[title] = [subject, "http://"+doi]
    
    subject = subject.replace(' ','_').replace(',','')
    
    if subject not in books_by_subject:
        books_by_subject[subject] = [(title, "http://"+doi)]
    else:
        books_by_subject[subject].append((title, "http://"+doi))

with open('dois.json', 'w+') as jf:
    json.dump(books, jf)
with open('books_by_subject.json', 'w+') as jf:
    json.dump(books_by_subject, jf)

## Build the Subject Enum
# for subject in books_by_subject:
#     subject_title = subject.replace(' ','_').replace(',','')
#     print(subject_title,"= '{}'".format(subject_title))

class SubjectsEnum:
    Engineering = 'Engineering'
    Humanities_Social_Sciences_and_Law = 'Humanities_Social_Sciences_and_Law'
    Mathematics_and_Statistics = 'Mathematics_and_Statistics'
    Behavioral_Science = 'Behavioral_Science'
    Biomedical_and_Life_Sciences = 'Biomedical_and_Life_Sciences'
    Chemistry_and_Materials_Science = 'Chemistry_and_Materials_Science'
    Medicine = 'Medicine'
    Business_and_Economics = 'Business_and_Economics'
    Earth_and_Environmental_Science = 'Earth_and_Environmental_Science'
    Physics_and_Astronomy = 'Physics_and_Astronomy'
    Computer_Science = 'Computer_Science'
    Behavioral_Science_and_Psychology = 'Behavioral_Science_and_Psychology'
    Energy = 'Energy'
    Business_and_Management = 'Business_and_Management'
    Religion_and_Philosophy = 'Religion_and_Philosophy'
    Economics_and_Finance = 'Economics_and_Finance'
    Education = 'Education'
    Law_and_Criminology = 'Law_and_Criminology'
    Social_Sciences = 'Social_Sciences'
    Literature_Cultural_and_Media_Studies = 'Literature_Cultural_and_Media_Studies'
    Intelligent_Technologies_and_Robotics = 'Intelligent_Technologies_and_Robotics'

    @classmethod
    def members(cls):
        
        attribs = filter(lambda attr: not attr[0].startswith('_'),
                         inspect.getmembers(cls))
        return [attr[1] for attr in attribs if not inspect.ismethod(attr[1])]

STOP_WORDS = {'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 
              'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they',
              'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 
              'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 
              'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 
              'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 
              'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 
              'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 
              'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 
              'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does',
              'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 
              'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 
              'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 
              'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 
              'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 
              'here', 'than'}

# =============================================================================
#%%   Prepare and run the scrapper over all of the contents
# =============================================================================
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class SpringerScrapper:
    
    path_gecko   = "C:\\Users\\Miguel\\Anaconda3\\Lib\\geckodriver.exe"
    download_dir = "C:\\Users\\Miguel\\Desktop\\programas_python\\springerScrapper\\downloaded"
    SAVE_ANYWAY  = True
    MAX_ITER     = 40
    WAIT_TIME    = 6 # seconds
    Download_Fail = {}
    GREATE_WEB_DRIVER = True # renaming already downloaded files does not require 
    
    def __init__(self, subject=''):
        self.book   = ''
        self.driver = None
        self.__initializeWebDriver(subject)
        
        self.counter = 0
    
    #===========================================================================
    #%%    HELPERS
    #===========================================================================
    def __wait(self):
        pass
    
    def __failed(self, msg=''):
        print(self.__progress()," [FAIL] cannot download '{}', reason: {}"
              .format(self.book, msg))
        self.driver.save_screenshot('error_download_{}_{}_({})_({}).png'
                                    .format(self.subject[:min(15, len(self.subject))], 
                                            self.counter, msg, self.current_doi))
        
    def __closeDriver(self):
        self.driver.close()
        self.driver = None
    
    def __progress(self):
        return "[{}/{}]".format(self.counter, len(books_by_subject[self.subject]))
    
    def __bookAlreadyDownloaded(self, subject=None):
        if self.SAVE_ANYWAY:
            return False
        files = [f for f in os.listdir(self.download_dir) 
                    if os.path.isfile(os.path.join(self.download_dir, f))]
        if subject:
            files = files + os.listdir(self.download_dir+'\\'+subject)
        
        _keyWords = self.book.translate(',-:').split()
        for filename in files:
            match_kw = map(lambda key: key in filename, _keyWords)
            #if all(map(lambda key: key in filename, _keyWords)):
                # not all filenames have the complete text of the title
            _r = list(filter(lambda i: i, match_kw))
            if len(list(filter(lambda i: i, match_kw))) >= min(4, len(_keyWords)):
                print(self.__progress(), 
                      "[SKIP] The book has already been downloaded:"
                      " '{}' <- keys: {}".format(filename, _keyWords))
                return True
        return False
        
    def __initializeWebDriver(self, subject=''):
        
        self.subject = subject
        
        options = Options()
        options.binary_location = self.path_gecko
        
        d_dwl = self.download_dir+'\\'+subject if subject else self.download_dir
        
        if not self.GREATE_WEB_DRIVER:
            return
        
        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.dir", d_dwl)
        profile.set_preference("browser.download.useDownloadDir", True)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        profile.set_preference("pdfjs.disabled", True) # disable the built-in PDF viewer
        
        self.profile = profile
        self.driver = webdriver.Firefox(executable_path= self.path_gecko,
                                        firefox_profile=profile)
    
    def __folderSaving(self, subject):
        
        if subject not in SubjectsEnum.members():
            raise Exception("subject [{}] is not valid".format(subject))
        
        if not os.path.exists(self.download_dir):
            os.mkdir(r'{}'.format(self.download_dir))
            
        if not os.path.exists(self.download_dir+'\\'+subject):
            os.mkdir(r'{}\\{}'.format(self.download_dir, subject))
            
        self.profile.set_preference("browser.download.dir", 
                                    self.download_dir+'\\'+subject)
        self.driver.firefox_profile
            
        
    #===========================================================================
    #%%     PRIVATE DOWNLOADER METHODS
    #===========================================================================
    def __accessToFirstPage(self):
        
        aux_a_tags = self.driver.find_elements(By.TAG_NAME, 'a')
        aux_a_tags = list(filter(lambda a: a.text != '', aux_a_tags))
        for tag_ in aux_a_tags:
            if 'download book pdf' == tag_.text.lower():
                try:
                    tag_.click()
                    accesed = self.__accessToPreview()
                    if (not accesed):
                        self.__failed('cannot access to the tag')
                        break
                    print(self.__progress(), " [DONE] ")
                    return
                except Exception as e:
                    self.__failed(' [FAIL] unexpected break')
                    print(str(e))
                    break
        self.__failed(' [FAIL] It has not "download book pdf" button.')
    
    def __accessToPreview(self):
        time.sleep(2)
        # get the last one (delete it)
        default_handle  = self.driver.current_window_handle
        window_download = self.driver.window_handles[1] 
        self.driver.switch_to_window(window_download)
        
# ------------------------------------------------------------------------------ 
#         ## This code was part of the downloading in case of opening the
#         ## preview, that estimates the time for download (deprecated)
#         iter_ = 0
#         pages = self.driver.find_elements(By.XPATH, '//*[@id="numPages"]')
#         if len(pages) == 0 or os.path(self.download_dir):
#             return False
#         while (pages[0].text == 'of 0') and (iter_ < self.MAX_ITER):
#             time.sleep(12)
#             iter_ += 1
#             pages = self.driver.find_elements(By.XPATH, '//*[@id="numPages"]')
#         
#         if (iter_ != self.MAX_ITER) or (pages[0].text != 'of 0'):
#             self.__download(iter_)
# ------------------------------------------------------------------------------ 
        self.__download()
        
        self.driver.close()
        self.driver.switch_to_window(default_handle)
        
        self.__wait()
        return True
        
    def __download(self):
        """ When we click the item, there is no need for the window to search
        the downloading button, so the method just waits until the 
        'file*.part disappears. """
#         aux_tags = self.driver.find_elements(By.XPATH, '//*[@id="download"]')
#         print(len(aux_tags))
#         aux_tags[0].click()
#         print("downloading [{}] [] s estimated"
#               .format(self.book, self.WAIT_TIME*(iterations+1)))
        iter_ = 0
        while self.__stillDownloading():
            time.sleep(self.WAIT_TIME) 
            # assuming download expend the same time as load
            if iter_ >= self.MAX_ITER:
                print("WARNING: It could not download the book "
                      "[{}], time exceeded {}s"
                      .format(self.book, self.WAIT_TIME*self.MAX_ITER))
                break
            iter_ += 1
    
    def __stillDownloading(self):
        download_dir = self.download_dir
        if self.subject:
            download_dir += '\\{}'.format(self.subject)
        
        return any(map(lambda f: f.endswith('.part'), os.listdir(download_dir)))
        
    #===========================================================================
    #%%     PUBLIC METHODS FOR DOWNLOAD (iterators)
    #===========================================================================
    ## Iterate over all the books ----------------------------------------------
    def downloadBySubject(self, subject):
        
        if not self.driver:
            self.__initializeWebDriver()
        
        self.__folderSaving(subject)
        
        print("Preparing to download [{}] books about '{}'"
                .format(len(books_by_subject[subject]), subject))
        
        for book, contents in books_by_subject[subject]:
            self.counter += 1
            print(self.__progress()," Downloading '{}' ...".format(book))
            self.book = book
            self.current_doi = contents
            if self.__bookAlreadyDownloaded(subject):
                continue
            try:
                self.driver.get(contents) # go to doi
            except WebDriverException as e:
                print(self.__failed("[FAIL] Could not reach the page"))
                print(str(e))
            time.sleep(6)
            self.__accessToFirstPage()
        
        self.__wait()
        self.driver.close()
    
    def renameFiles(self):
        """ After the download, the filename has the form: 
            'YEAR_Book_CamelShortcutOfTitle.pdf'"""
        f_path = self.download_dir + '\\' + self.subject
        book_list = os.listdir(f_path)
        
        self._booksBySubject = deepcopy(books_by_subject[self.subject])
        
        transformed = {}
        not_transformed = list(map(lambda x: x[0], self._booksBySubject))
        self.__wait()
        for file_ in book_list:
            if file_[:2] not in ('19','20'):
                print("Book '{}' already formatted".format(file_))
                continue
            
            year, _, title = file_.split('_')
            title = title.replace('.pdf','')
            
            gotit = False
            for index, tupl_ in enumerate(self._booksBySubject.copy()):
                _bool_is_the_book, book = self.__filterBookName(title, tupl_)
                if _bool_is_the_book:
                    #replace(' ', '_')
                    new_name = book + " ({}).pdf".format(year)
                    new_name = _filterIllegal(new_name)
                    try:
                        os.rename(f_path+'\\'+file_, f_path+'\\'+new_name)
                    except BaseException as b:
                        print("ERROR:\n", b) # skip 
                    gotit = True
                    transformed[book] = (file_, new_name)
                    
                    #if book in not_transformed:
                    not_transformed.remove(book)
                    break
            if gotit:
                del self._booksBySubject[index]
        
        self.__checkRenaming(transformed, not_transformed, f_path)
    
    def __filterBookName(self, title, tuple_book):
        book, _ = tuple_book
        #_keyWords = book.translate(',-:').split()
        _keyWords = _mergeStopWords(book)
        
        _match = list(map(lambda key: key in title, _keyWords))
        if _match[-1] == False:
            _match.pop() # Last word is split, 
        _lenTrue = len(list(filter(lambda i: i, _match)))
        _lenMin =  max(2, round(len(_keyWords)/2 + 0.1))
        return (_lenTrue >= _lenMin, book)
    
    renaming_log_filename = 'log_rename.txt'
    
    def __checkRenaming(self, transformed, not_transformed, f_path):
        """ 
        :transformed <dict> (previous_value, new_value)"""
        book_list = list(filter(lambda f: f.startswith('20'), os.listdir(f_path)))
        
        if not self.__logRenamedFiles(f_path, transformed, not_transformed):
            return
        
        correct = False
        print("Check if all the titles for {} are correct:".format(self.subject))
        while(not correct):
            correct = '1'
            print("Are all correct?, type 0 for False, nothing or 1 for True")
            correct = bool(int(correct)) if correct else True
            if correct:
                break
            
            while (not correct):
                check = dict([(it[0], it[1]) for it in enumerate(transformed.items())])
                print('  ind\t Original Title  ->  New Value ')
                for i, item_ in check.items():
                    print('  ',i,'.\t', item_[0],'  ->  ', item_[1])
                
                i_change   = input("Put the index:  ")
                val_change = input("Put the title:  ")
                
                transformed[check[i_change][0]] = val_change
                correct = bool(input(" Are more errors? (type 1 if not, otherwise pass)"))
    
    def __logRenamedFiles(self, f_path, transformed, not_transformed):
        
        try:
            with open(f_path+'\\'+self.renaming_log_filename, 'w+') as f:
                pass
            with open(f_path+'\\'+self.renaming_log_filename, 'a+') as f:
                f.write("\n = Changed filenames    =====\n")
                f.write('\n'.join(map(lambda x: "{} -> {}".format(*x), transformed.values())))
                f.write("\n = not transformed titles =====\n")
                f.write('\n'.join(not_transformed))
                
                print("\n = Changed filenames    =====")
                print('\n'.join(map(lambda x: "{} -> {}".format(*x), transformed.values())))
                print(" = not transformed titles =====")
                print('\n'.join(not_transformed))
        except BaseException as b:
            print("ERROR:\n",
                  "[{}] Non Unicode char, breaks rename file\n".format(self.subject),
                  b)
            print("\n".join(not_transformed))
            return False
        return True
#===============================================================================
#%%     HELPERS
#===============================================================================
_ILLEGAL = ['NUL','\',''//',':','*','"','<','>','|']
def _filterIllegal(title):
    for i in _ILLEGAL:
        title = title.replace(i, '_')
    return title

_TRANSLATE = [s for s in ',.-:;?¿!¿~@|¬\\']
def _mergeStopWords(title):
    for s in _TRANSLATE:
        title = title.replace(s, ' ')
    title = title.split()
    w_main = []
    for w in title:
        if w.lower() in STOP_WORDS:
            continue
        w_main.append(w)
    return w_main

def downloadAll():
    """ Problems with the individual subject folder modification, 
    this loop iterates over all subjects
    """
    _subjects = SubjectsEnum.members()
    for subject in SubjectsEnum.members(): 
        print("\n-------------------------------------------------------------")
        if os.path.exists(SpringerScrapper.download_dir+'\\'+subject):
            files = os.listdir(SpringerScrapper.download_dir+'\\'+subject)
            files = [f for f in files if all(par in f for par in ('(', ')'))]
            if len(files) >=  len(books_by_subject[subject]):
                print("All contents for [", subject,"] has been downloaded")
                continue
        print("Downloading all of subject '{}'".format(subject))
        spr_driver = SpringerScrapper(subject)
        spr_driver.downloadBySubject(subject)
        
        ## Rename to the complete title while in the folder.
        #spr_driver.renameFiles()
        
    print("\n\nAll books downloaded, you filthy pirate\n   Bye ...")


def renameAll():
    """ Problems with the individual subject folder modification, 
    this loop iterates over all subjects
    """
    _subjects = SubjectsEnum.members()
    for subject in SubjectsEnum.members(): 
        print("\n-------------------------------------------------------------")
        if not os.path.exists(SpringerScrapper.download_dir+'\\'+subject):
            print("Subject '{}' has not been downloaded".format(subject))
            continue
        print("Renaming subject '{}'".format(subject))
        SpringerScrapper.GREATE_WEB_DRIVER = False
        spr_driver = SpringerScrapper(subject)
        
        ## Rename to the complete title while in the folder.
        spr_driver.renameFiles()
        
    print("\n\nRenamed, check non renamed files in console output\n   Bye ...")
#===============================================================================
#%%     MAIN
#===============================================================================
if __name__ == '__main__':
    
#     subject = SubjectsEnum.Engineering
#     spr_driver = SpringerScrapper(subject)
#     spr_driver.downloadBySubject(subject)
    
    
    #downloadAll()
    renameAll()
