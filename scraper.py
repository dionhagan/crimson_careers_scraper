#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Dion Hagan
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The Crimson Careers Scraper is a tool for scraping Harvard's Career website.

Usage:
>>> from scraper import CrimsonScraper
>>> cc = CrimsonScraper(my_email, my_huid)
>>>
>>> cc.run(letter='E') # scrape last names starting with 'E', store results in 'E.csv'
>>> cc.run(first='B', last='W') # scrape last names starting with 'B' to names starting with 'W'
"""

import sys
import time
import pandas as pd
from os import listdir
from collections import defaultdict as ddict

# import selenium libraries
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


BASE_URL = 'https://harvard-csm.symplicity.com/students/?_alpha=%c&_so_clear_paging=1&s=employers&ss=mini_contacts'

class CrimsonScraper(object):

    def __init__(self, email, huid):
        self.usr = email
        self.pwd = huid
        self.url = BASE_URL
        self.contacts = {chr(k): ddict(list) for k in xrange(65, 91)}
        self.contactsdf = pd.DataFrame()


    def login(self, d, letter='A'):
        # fetch login page
        d.get(self.url % letter)

        print 'logging in....'

        # select login elements
        usr = d.find_element_by_id('username')
        pwd = d.find_element_by_id('password')
        lgn = d.find_element_by_css_selector('.input-submit')

        # log in
        usr.send_keys(self.usr)
        pwd.send_keys(self.pwd)

        lgn.click()
        print 'initializing scraper...'
        print '\n'

    def check_exists(self, attr, d, attr_type='xpath'):
        try:
            if attr_type == 'xpath':
                d.find_element_by_xpath(attr)
            elif attr_type == 'css':
                d.find_element_by_css_selector(attr)
        except NoSuchElementException:
            return False
        return True

    def get_info(self, elements, d, letter):
        # get num elements
        count = len(elements) + 1

        # Find Contact Info for all people listed on the page
        for i in range(1,count):

            # Get Names
            if self.check_exists('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[1]/a' % i, d):
                tmp_name = d.find_element_by_xpath('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[1]/a' % i).text.encode('UTF-8')
                tmp_name = str(tmp_name)
            else:
                tmp_name = ''

            # Get Companies
            if self.check_exists('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[2]/p/a' % i, d):
                tmp_company = d.find_element_by_xpath('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[2]/p/a' % i).text.encode('UTF-8')
                tmp_company = str(tmp_company)
            else:
                tmp_company = ''

            # Get Email Addresses
            if self.check_exists('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[3]' % i, d):
                tmp_email = d.find_element_by_xpath('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[3]' % i).text.encode('UTF-8')
                tmp_email = str(tmp_email)
            else:
                tmp_email = ''

            # Get Phone Numbers 
            if self.check_exists('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[4]' % i, d):
                tmp_phone = d.find_element_by_xpath('//*[@id="_list_form"]/ul/li[%d]/div[1]/div[4]' % i).text.encode('UTF-8')
                tmp_phone = str(tmp_phone)
            else:
                tmp_phone = ''

            # debug: 
            # print '%s\t %s\t %s\t %s' % (tmp_name, tmp_company, tmp_email, tmp_phone)
                    
            # update data with current page
            self.contacts[letter]['Name'].append(tmp_name)
            self.contacts[letter]['Company'].append(tmp_company)
            self.contacts[letter]['Email'].append(tmp_email)
            self.contacts[letter]['Phone'].append(tmp_phone)

    def csv_version(self):
        # default csv file name
        default = "contacts"

        # search current directory for .csv files to find current version
        files = listdir('./')
        max_v = 0
        for file in filter(lambda f: '.csv' in f, files):
            print file
            # get name of file minus .csv
            file_name = file[0:-4]
            try:
                # get last version of csv
                version = int(file_name[-1])
                max_v = max(max_v, version)
            except ValueError:
                # last character not an integer -> no version yet
                pass
        if max_v != 0:
            # update default if max version >= 1
            default = 'contacts-%d' % (max_v + 1)
        return default

    def export_csv(self, letter=None):

        # create empty pandas df to store results
        df = pd.DataFrame()

        if not letter:
            # get csv file version
            filename = self.csv_version() + '.csv'

            # loop through all letters and merge into dataframe
            for key in self.contacts.keys():
                df = df.append(pd.DataFrame(self.contacts[key]))
            # save df to file
            print df.head()
            print '\n'
            print 'saving results to %s' % filename
            df.to_csv(filename, columns=['Company','Name','Email','Phone'])
        else:
            df = df.append(pd.DataFrame(self.contacts[letter]))
            print df.head()
            print '\n'
            print 'saving results to %c.csv' % letter
            df.to_csv('%c.csv' % letter, columns=['Company','Name','Email','Phone'])

        # update obj copy
        self.contactsdf = df

    def scrape(self, pgnum, d, letter):
        try:    
            print 'loading %c (p. %d)' % (letter, pgnum)

            # check for next button
            if self.check_exists('.lst-next-btn', d, attr_type='css'):

                # Find number of contacts on page
                n = d.find_elements_by_css_selector('.list-item')
                if n == 0:
                    print 'no elements found on this page\n'; return

                # extract contact info and store in self.contacts
                self.get_info(n, d, letter)

                # navigate to next page
                try:
                    nxt = d.find_element_by_css_selector('.lst-next-btn')
                    nxt.click()
                except NoSuchElementException:
                    pass

                pgnum += 1
                time.sleep(1.6)

                # recurse to next page
                self.scrape(pgnum, d, letter)
            else:
                pass
        finally:
            pass

    def run(self, first='A', last='Z', letter=None):
        # initialize webdriver
        print 'starting Firefox...'
        d = webdriver.Firefox()
            
        #try:
        # let the games begin
        if letter:
            if first != 'A': 
                print 'Choose either a single letter or a first letter range to search from'
                return
            # login to page
            self.login(d, letter=letter)
            print 'initializing scraper...'

            # search specific letter
            self.scrape(1, d, letter)

            # sleep as to not timeout
            time.sleep(10)

            self.export_csv(letter)
        else:
            # login
            self.login(d, letter=first)

            # search first-last
            for i in xrange(ord(first), ord(last)+1):
                # convert int to letter
                letter = chr(i)
                if letter != first:
                    d.get(self.url % letter)
                self.scrape(1, d, letter)
                
                # sleep 10 sec to avoid timeout: 
                time.sleep(10)

            self.export_csv()


        # save and exit gracefully
        d.quit()
        print "finished!"
        return

