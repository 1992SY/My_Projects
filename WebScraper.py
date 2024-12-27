import requests
from bs4 import BeautifulSoup

page = requests.get("https://quotes.toscrape.com", verify=False)
contents = page.content
print(contents)
page.status_code
soup = BeautifulSoup(page.content)
print(soup)
soup.link
soup.link['href']
soup.span
soup.span['text']
soup.find(class_='text')
soup.find_all(class_='quote')
soup.find(class_='quote').a['href']
soup.find_all(class_='text')
soup.find_all(class_=['text','author'])

quoteList = []

for e in soup.find_all(class_="quote"):
    author = e.find(class_="author").getText()
    text = e.find(class_="text").getText()
    quoteList.append([author,text])
print(quoteList)

url = "https://quotes.toscrape.com/page/"

quoteList = []

for i in range(0,4):
    cur_url = "https://quotes.toscrape.com/page/" +str(i)
    page = requests.get(cur_url, verify=False)

    contents = page.content
    soup = BeautifulSoup(contents)

    for e in soup.find_all(class_="quote"):
        author = e.find(class_="author").getText()
        text = e.find(class_="text").getText()
        quoteList.append([author,text])

print(quoteList)
print(len(quoteList))
url = "https://quotes.toscrape.com/page/"

quoteList = []

# iterate over all pages of the URL
for i in range(0,4):
    cur_url = "https://quotes.toscrape.com/page/" +str(i)
    page = requests.get(cur_url)

# extract and parse the pages content
    contents = page.content
    soup = BeautifulSoup(contents)
    
# break out of the loop if there is no 'Next' button
    if soup.find(text = "Next ") == None:
        break

#iterate over all tags of class 'quote'
    for e in soup.find_all(class_="quote"):
        author = e.find(class_="author").getText()
        text = e.find(class_="text").getText()
        quoteList.append([author,text])

print(quoteList)
print(len(quoteList))
import re

txt = "The rain in Germany"

re.findall("^The.*Germany$", txt)
# create sample HTML
email_example = """<br/>
    <div>
        This is an example HTML document to showcase
        how email adresses can be retrieved using regex
    </div>
    tutor@iu.org
    <div>student@iu.org</div>
    <span>professor@iu.org</span>
"""
# parse the HTML
soup = BeautifulSoup(email_example,"lxml")
# compile a RegEx
regex = re.compile("\w+@\w+\.\w+")
# use the RegEx to extract email addresses from
# the HTML
print(soup.find(text = regex))
# load packages
from selenium import webdriver
# specifiy a webdriver
browser = webdriver.Edge()
# use the browser to go to a web page
browser.get('http://quotes.toscrape.com/')
# maximize the window
browser.maximize_window()
# use a simple script to scroll down 2000 pixels
browser.execute_script("window.scrollTo(0, 2000)")
# locate the next button
next_button = browser.\
find_element_by_partial_link_text('Next')
# click the next button
next_button.click()
!pip install selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
path_to_driver = r'C:/Users/yazidi/OneDrive - SIG PLC/Desktop/msedgedriver.exe'
service = Service(executable_path=path_to_driver)
driver = webdriver.Edge(service=service)
driver.get("http://www.python.org")
search_box = driver.find_element_by_name("q")
search_box.clear()
search_box.send_keys("getting started with python")
search_box.send_keys(Keys.RETURN)
driver.quit()

