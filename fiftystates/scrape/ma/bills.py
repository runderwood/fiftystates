from __future__ import with_statement
import datetime as dt

from fiftystates.scrape import ScrapeError
from fiftystates.scrape.tx import metadata
from fiftystates.scrape.tx.utils import chamber_name, parse_ftp_listing
from fiftystates.scrape.bills import BillScraper, Bill

import lxml.html
import urllib
import urllib2
from math import ceil
import re


class MABillScraper(BillScraper):
    state = 'ma'
    _bill_search_chunk_sz = 500
    _last_doctype = None

    def scrape(self, chamber, session):
        self.validate_session(session)

        search_base_url = 'http://malegislature.gov/Bills/SearchResults?'
        search_params = dict([
            ('Input.Keyword', ''),('Input.BillNumber',''),('Input.Subject',''),
            ('Input.City',''),('Input.DocumentTypeId',''),('Input.CommitteeId',''),
            ('x',36),('y', 25),('p', 1),('pgCount',100)])
        search_doctypes = [('Agency Filing', 1),('Amendment', 2),
            ('Bill', 3),('Communication', 4),('Letter of Transmittal', 5),
            ('Printed Document', 6),('Proposal', 7),('Recommendation', 8),
            ('Reorganization Plan', 9),('Report',10),('Resolution',11),
            ('Resolve',12),('Study Order',13),('Veto',14)]
        search_relevant_types = (2,3,11,12)

        for doctype in search_doctypes:
            doctype_name,doctype_id = doctype
            self._last_doctype = doctype_name
            if doctype_id not in search_relevant_types:
                continue
            search_params['Input.DocumentTypeId'] = doctype_id
            search_offset = 0
            search_chunksz = self._bill_search_chunk_sz
            search_params['pgCount'] = search_chunksz
            search_results_found = True
            while search_results_found:
                page = int(ceil(search_offset / search_chunksz) + 1)
                search_params['p'] = page
                search_url = search_base_url+urllib.urlencode(search_params)
                page = self.urlopen(search_url)
                root = lxml.html.fromstring(page)
                root.make_links_absolute(search_url)
                result_els = root.xpath('//table[@id="results"]')
                if len(result_els) < search_chunksz:
                    search_results_found = False
                for result_el in result_els:
                    search_offset = search_offset + 1
                    chamber, bill_url = self.parse_search_result(result_el)
                    if chamber:
                        self.scrape_bill(chamber, session, bill_url)
                    else:
                        continue

    def scrape_bill(self, chamber, session, url):
        page = self.urlopen(url)
        root = lxml.html.fromstring(page)
        bill_detail_el = root.xpath('//div[@class="col2"]//div[@class="Columns bg2717"]//div[@class="widgetContent"]')[0]
        title = bill_detail_el.xpath('.//p/text()')[0]
        bill_id = bill_detail_el.xpath('./p/b/text()')[1].strip()
        m = re.search('Bill Number: ([HSD0-9]+)', bill_id)
        if len(m.groups()):
            bill_id = m.groups()[0]
        else:
            bill_id = None
        doctype = None
        if self._last_doctype:
            doctype = self._last_doctype.lower()
        bill = Bill(session, chamber, bill_id, title, type=doctype)
        sponsors_el = bill_detail_el.xpath('./p[2]/a/text()')
        for i in range(len(sponsors_el)):
            sponsor = sponsors_el[i]
            if i == 0:
                type = 'primary'
            else:
                type = 'cosponsor'
            bill.add_sponsor(type, sponsor)
        secondary_sponsors_el = bill_detail_el.xpath('.//div[@class="dataBlock"]//td/a/text()')
        for secondary_sponsor in secondary_sponsors_el:
            bill.add_sponsor('secondary', secondary_sponsor)
        print bill
        self.save_bill(bill)

    def parse_search_result(self, result_el):
        file_el = result_el.xpath('.//td[@class="file"]')[0]
        file_no = file_el.xpath('.//ul[@class="fileNo"]//li/b/text()')[0].strip()
        m = re.search('([A-Z]{1,})([0-9]+)', file_no)
        chamber = None
        if m:
            if len(m.groups()) == 2:
                chamber_sig,bill_sig = m.groups()
                if chamber_sig[0] == 'H':
                    chamber = 'lower'
                elif chamber_sig[0] == 'S':
                    chamber = 'upper'
        else:
            m = re.search('([0-9]+', file_no)
            if m:
                chamber = 'joint'
        bill_url = result_el.xpath('.//td[@class="btn"]//a/@href')[0]
        return (chamber, bill_url)
