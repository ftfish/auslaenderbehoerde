import datetime
import sys
import threading
from pprint import pprint

import bs4 as bs
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineCore import QWebEngineHttpRequest
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QApplication, qApp


class Client(QWebEnginePage):
    """
    A thin subclass of an QWebEnginePage offering *synchronized* page load functionality. This acts as a web client or browser.
    """
    def __init__(self):
        """
        Initialize the client. It defines and initializes some internal data.
        """
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.loadedSem = threading.Semaphore(0)
        self.html = None
        self.loadFinished.connect(self.on_page_load)

        # uncomment the following to see the cookies get printed
        # self.profile().cookieStore().cookieAdded.connect(self.on_cookie_add)

    @staticmethod
    def on_cookie_add(cookie):
        """ Callback function that gets called when a cookie is set."""
        print(cookie.toRawForm())

    def on_page_load(self):
        """Callback function that gets called when a page finished loading"""
        # print('load finished')

        def set_source(html):
            """ Store the source as an attribute and signals the source is available through a semaphore."""
            # print('setting source')
            self.html = html
            self.loadedSem.release()
            qApp.quit()

        # toHtml() is asynchronous. It calls a callback function with the html as argument when the source is ready
        self.toHtml(set_source)

    def myload(self, urlOrRequest):
        """A convenient method that loads a QUrl or a QWebEngineHttpRequest. It blocks until the source is ready."""
        self.load(urlOrRequest)
        qApp.exec_()
        self.loadedSem.acquire()


def getSelectedDate(html):
    """A function that parses an html and returns the current selected date as a datetime.date object."""
    soup = bs.BeautifulSoup(html, 'lxml')
    text = soup.find(id='selectedDate').attrs['value']
    import datetime
    return datetime.datetime.strptime(text, '%Y-%m-%d').date()


def loadDate(client, date):
    """Load the page for a date and blocks until the html is ready"""
    url = 'https://otv.karlsruhe.de/terminmodul/live/termin/index'
    dateStr = date.strftime('%Y-%m-%d')
    req = QWebEngineHttpRequest.postRequest(QUrl(url), {'selectedDate': dateStr,
                                                        'baseUrl': '/terminmodul/live'})
    client.myload(req)


def getAvailableTimes(html):
    """"Get the list of free time slots from the html of a day"""
    soup = bs.BeautifulSoup(html, 'lxml')
    table = soup.find('table', id='tabelleTermine')
    timeLinks = table.findAll('a')

    import re
    times = [re.findall('datum/(\d+)-(\d+)-(\d+)/stunde/(\d+)/minute/(\d+)', link.attrs['href'])[0] for link in timeLinks]

    return ['%d:%.2d' % (int(time[-2]), int(time[-1])) for time in times]


def getAvailableTimesOnDate(client, date):
    """Function that first loads the page for a date and then returns the list of free time slots on that day."""
    loadDate(client, date)
    return getAvailableTimes(client.html)


def findFirst(L, pred):
    """
    Returns the first element in L that satisfies a given predicate with binary search.
    L must be a list of elements that DO NOT satisfy the predicate followed by a list of ones that DO satisfy pred.
    Returns 0 if there is no element satisfying pred.
    """
    left, right = 0, len(L) - 1
    ans = 0
    while left <= right:
        mid = left + (right - left) // 2
        if pred(L[mid]):
            ans = L[mid]
            right = mid - 1
        else:
            left = mid + 1

    return ans


def isWanted(client, date):
    """Check if the page of a date contains free time slots."""
    loadDate(client, date)
    times = getAvailableTimes(client.html)
    ret = len(times) > 0
    print('\tinspecting date', date, ', result =', 'available!!' if ret else 'full')
    return ret


def getPossibleDays(html):
    """Get a list of possible days on a page. Holidays and weekends are not included

    The current code is NOT working correctly as the page contains <noscript> tags. This function is not used.
    """
    print(html, file=open('source2.html', 'w', encoding='utf8'))
    soup = bs.BeautifulSoup(client.html, 'lxml')
    tag = soup.find(id='divKalenderTerminuebersicht')
    # get all days in the current month
    days = tag.findAll(class_='current-month')
    pprint(list(days))

    # remove all disabled days from current month
    days = filter(lambda d: 'disabled' not in d.attrs['class'], days)

    ret = [int(d.text) for d in days]

    print(ret)
    return ret


def getHolidays(date):
    """
    Get a list of public holidays given a datetime.date object.
    This method does so by crawling a specific module on the website.
    """
    import requests, itertools
    url = 'https://otv.karlsruhe.de/terminmodul/live/kalender/getfeiertagejsonformonth/monat/%02d/jahr/%d' % (date.month, date.year)
    response = requests.request('get', url).json()
    # print(response)
    ret = itertools.chain.from_iterable(dict(v).keys() for v in response.values())
    return list(ret)


if __name__ == '__main__':
    client = Client()

    # load service selection page
    url = 'https://otv.karlsruhe.de/terminmodul/live/index/index/dienststelle/38'
    client.myload(QUrl(url))
    # print(client.html)

    # choose application and load calendar page
    calendarUrl = 'https://otv.karlsruhe.de/terminmodul/live/dienstleistung/save'
    req = QWebEngineHttpRequest.postRequest(QUrl(calendarUrl), {'dienstleistungsid[]': '460',
                                                                'personenzahl[460]': '1',
                                                                'personenzahl[458]': '1',
                                                                'bemerkung': '',
                                                                'anmeldung_action': '1',
                                                                'lang': 'de',
                                                                'weiter': 'Weiter: Terminauswahl'
                                                                })

    client.myload(req)


    # get all possible days (excluding weekends and holidays) within 90 days
    startDate = getSelectedDate(client.html)
    holidays = set(getHolidays(startDate) + getHolidays(startDate + datetime.timedelta(days=60)))
    possibleDates = []
    for dayDelta in range(90):
        date = startDate + datetime.timedelta(days=dayDelta)
        if date.isoweekday() <= 5 and date.strftime('%Y-%m-%d') not in holidays:
            possibleDates.append(date)

    print('Using binary search to find first sure date...')
    firstSureDate = findFirst(possibleDates, lambda date: isWanted(client, date))

    print('First sure date:', firstSureDate, getAvailableTimesOnDate(client, firstSureDate))

    print('Trying to find earlier free slots...')
    found = 0
    for date in possibleDates:
        if date >= firstSureDate:
            break
        if isWanted(client, date):
            print('possible earlier date:', date, getAvailableTimes(client.html))
            found += 1

    print('Found %d earlier dates.' % found)

    qApp.quit()
