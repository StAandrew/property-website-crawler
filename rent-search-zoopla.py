import datetime
import time 
import pytz
import sys
import pickle
import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from random import randrange
from urllib.request import urlopen, Request
from hashlib import sha256
import credentials
from maps_distance_finder import distance_from_work
  
MY_ADDRESS = credentials.MY_ADDRESS
MY_PASSWORD = credentials.MY_PASSWORD
TO_ADDRESS = 'xxxxxxx@somemail.com'
MY_URL = 'https://www.zoopla.co.uk/to-rent/property/wc1e/?beds_min=3&page_size=200&price_frequency=per_month&price_max=2000&price_min=1250&view_type=list&q=WC1E%20%20Bloomsbury%2C%20Gray%27s%20Inn&radius=5&results_sort=newest_listings&search_source=refine'
# MY_URL = 'https://www.zoopla.co.uk/to-rent/property/wc1e/?beds_min=3&page_size=25&price_frequency=per_month&price_max=2000&price_min=1250&view_type=list&q=WC1E%20%20Bloomsbury%2C%20Gray%27s%20Inn&radius=3&results_sort=newest_listings&search_source=refine'
PROD = 1
movein_date_limit = datetime.datetime.strptime('1 Aug 2022', '%d %b %Y')

class Property():
    def __init__(self, price=0, title='', address='', link='', agency=''):
        self.price = price
        self.title = title
        self.address = address
        self.link = link
        self.agency = agency
        self.hash = ''
        self.notify = 0
        self.added = time.strftime("%H:%M:%S", time.localtime()) + ', ' + datetime.datetime.now(pytz.timezone('Europe/Vilnius')).strftime('%z')


    def set_hash(self):
        if self.address != '' and self.price != '' and self.title != '':
            to_hash = self.address + self.price + self.title.replace(" ", "")
            to_hash = bytearray(to_hash, 'utf-8')
            self.hash = sha256(to_hash).hexdigest()
        else:
            self.hash = 0


class SavedProperties():

    def __init__(self, data=[]):
        self.arr = data


    def add_property(self, price, title, address, link, agency):
        if title == '' or price == '':
            return
        new_property = Property(price, title, address, link, agency)
        new_property.set_hash()
        new_property.notify = 1
        for p in self.arr:
            if (p.hash == new_property.hash):
                return
        if new_property.agency != '':
            if 'mb-property-services-london' in new_property.agency:
                new_property.notify = 0

        if new_property.notify == 1:
            s = login()
            msg_title = 'Z: ', price + ' ' + title
            msg_body = address + '\n'
            msg_body += agency + '\n'
            msg_body += link + '\n'
            send_notification(s, str(msg_title), str(msg_body))
        self.arr.append(new_property)


    def list_properties(self):
        text = ''
        for item in self.arr:
            attrs = vars(item)
            text += '\n'.join("%s: %s" % item for item in attrs.items())
            text += '\n\n'
        return text


    def clear_list(self):
        self.arr.clear()


def login():
    try:
        s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
        s.ehlo()
        s.login(MY_ADDRESS, MY_PASSWORD)
        return s
    except:
        exit("Email login error")

def send_notification(s, subject, message):
    if PROD:
        msg = MIMEMultipart()
        msg['From'] = MY_ADDRESS
        msg['To'] = MY_ADDRESS
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))
        s.send_message(msg)

        del msg
        print('Notified of ' + subject + ' at ' + time.strftime("%H:%M:%S", time.localtime()) + ', ' + datetime.datetime.now(pytz.timezone('Europe/Vilnius')).strftime('%z'))
    else:
        print('DEV ENVIRONMENT: Notified of ' + subject + ' at ' + time.strftime("%H:%M:%S", time.localtime()) + ', ' + datetime.datetime.now(pytz.timezone('Europe/Vilnius')).strftime('%z'))


def load_properties(filename):
    try:
        with open(filename, 'rb') as filehandle:
            data = pickle.load(filehandle)
        return data
    except:
        return []


def save_properties(filename, data):
    with open(filename, 'wb') as filehandle:
        pickle.dump(data, filehandle)


def remove_file(filename):
    try:
        if os.path.isfile(filename):
            os.remove(filename)
    except:
        pass


def save_html_to_file(data):
    file = open('rent-search.txt', 'w')
    file.write(data)
    file.close()


def fetch_data(link=MY_URL):
    url = Request(link, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    return(html)


def get_total_found(html):
    soup = BeautifulSoup(html , 'html.parser')
    number_str = soup.select("p[class^=css-ic7tm6]")[0].text
    number_str = number_str.replace(" results", "")
    try:
        return int(number_str)
    except (ValueError, TypeError):
        return 0


def get_prices(html):
    prices = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.select("p[class^=css-1w7anck]")
    for el in arr:
        prices.append(el.text.replace(' pcm','').replace(",", "")[1:])
    return prices


def get_titles(html):
    titles = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.select("h2[class^=css-sbwlc4-Heading2]")
    for el in arr:
        titles.append(el.text.strip())
    return titles


def get_addresses(html):
    addresses = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.findAll("p", {"data-testid": "listing-description"})
    for el in arr:
        addresses.append(el.text.strip())
    return addresses


def get_links(html):
    links = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.findAll("a", {"data-testid": "listing-details-image-link"})
    for el in arr:
        link = "https://zoopla.co.uk" + el.get('href')
        links.append(link)
    return links


def get_agencies(html):
    agencies = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.findAll("a", {"data-testid": "listing-details-agent-logo"})
    for el in arr:
        agencies.append('https://zoopla.co.uk' + el.get('href'))
    return agencies


def get_descriptions(html):
    descriptions = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.findAll("span", {"itemprop": "description"})
    for el in arr:
        descriptions.append(el.text)
    return descriptions


def get_movein_dates(html):
    movein_dates = []
    soup = BeautifulSoup(html , 'html.parser')
    arr = soup.findAll('div', {'data-testid': 'search-result'})
    for el in arr:
        date_el = el.find("span", {"data-testid": "available-from-date"})
        if not date_el is None:
            str_date = date_el.text.replace('\xa0', '').replace('th', '').replace('st', '').replace('nd', '')
            if str_date == 'immediately':
                datetime_object = datetime.datetime.strptime('1 Jan 2000', "%d %b %Y")
                movein_dates.append(datetime_object)
            else:
                datetime_object = datetime.datetime.strptime(str_date, "%d %b %Y")
                movein_dates.append(datetime_object)
        else:
            datetime_object = datetime.datetime.strptime('1 Jan 2025', "%d %b %Y")
            movein_dates.append(datetime_object)
    return movein_dates


def get_property_location(html):
    soup = BeautifulSoup(html, 'html.parser')
    script_text = soup.find('script').get_text()
    # relevant = script_text[script_text.index('=') + 1:]
    geo = json.loads(script_text)['@graph'][3]['geo']
    lat = geo['latitude']
    lng = geo['longitude']
    return f'{lat}, {lng}'


def get_distance(property_link):
    property_website = fetch_data(property_link)
    location = get_property_location(property_website)
    return distance_from_work(location)


def main():
    filename = 'properties_zoopla'

    while True:
        data = load_properties(filename)
        saved_properties = SavedProperties(data)

        html = fetch_data()
        total_available = get_total_found(html)

        prices_all = get_prices(html)
        titles_all = get_titles(html)
        addresses_all = get_addresses(html)
        links_all = get_links(html)
        agencies_all = get_agencies(html)
        movein_dates_all = get_movein_dates(html)

        for i in range(total_available):
            if movein_dates_all[i] > movein_date_limit:
                biking_dist = get_distance(links_all[i])
                if biking_dist < 60*30 or int(prices_all[i]) < 1800:
                    saved_properties.add_property(prices_all[i], titles_all[i], addresses_all[i], links_all[i], agencies_all[i])

        save_properties(filename, saved_properties.arr)

        to_sleep = 180 + randrange(90)
        time.sleep(to_sleep)


if __name__ == '__main__':
    main()
