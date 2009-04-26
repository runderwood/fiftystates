#!/usr/bin/env python
import datetime as dt
from cStringIO import StringIO
from lxml import etree

from sqlalchemy import (Table, Column, Integer, String, ForeignKey,
                        DateTime, Text, desc, create_engine,
                        UnicodeText)
from sqlalchemy.orm import sessionmaker, relation, backref
from sqlalchemy.ext.declarative import declarative_base

# ugly hack
import sys
sys.path.append('./scripts')
from pyutils.legislation import LegislationScraper, NoDataForYear

# Code for handling California's legislative info SQL dumps
# You can grab them from http://www.leginfo.ca.gov/FTProtocol.html

Base = declarative_base()

class Bill(Base):
    __tablename__ = "BILL_TBL"
    
    bill_id = Column(String(19), primary_key=True)
    session_year = Column(String(8))
    session_num = Column(String(2))
    measure_type = Column(String(4))
    measure_num = Column(Integer)
    measure_state = Column(String(40))
    chapter_year = Column(String(4))
    chapter_type = Column(String(10))
    chapter_session_num = Column(String(2))
    chapter_num = Column(String(10))
    latest_bill_version_id = Column(String(30))
    active_flg = Column(String(1))
    trans_uid = Column(String(30))
    trans_update = Column(DateTime)
    current_location = Column(String(200))
    current_secondary_loc = Column(String(60))
    current_house = Column(String(60))
    current_status = Column(String(60))

    @property
    def short_bill_id(self):
        return "%s%d" % (self.measure_type, self.measure_num)
    
class BillVersion(Base):
    __tablename__ = "BILL_VERSION_TBL"

    bill_version_id = Column(String(30), primary_key=True)
    bill_id = Column(String(19), ForeignKey(Bill.bill_id))
    version_num = Column(Integer)
    bill_version_action_date = Column(DateTime)
    bill_version_action = Column(String(100))
    request_num = Column(String(10))
    subject = Column(String(1000))
    vote_required = Column(String(100))
    appropriation = Column(String(3))
    fiscal_committee = Column(String(3))
    local_program = Column(String(3))
    substantive_changes = Column(String(3))
    urgency = Column(String(3))
    taxlevy = Column(String(3))
    bill_xml = Column(UnicodeText)
    active_flg = Column(String(1))
    trans_uid = Column(String(30))
    trans_update = Column(DateTime)

    bill = relation(Bill, backref=
                    backref('versions',
                            order_by=desc(bill_version_action_date)))

    @property
    def xml(self):
        if not '_xml' in self.__dict__:
            self._xml = etree.parse(StringIO(self.bill_xml.encode('utf-8')))
        return self._xml

    @property
    def title(self):
        texts = self.xml.xpath("//*[local-name() = 'Title']//text()")
        title = ''.join(texts).strip().encode('ascii', 'replace')
        return title

class CASQLImporter(LegislationScraper):
    state = 'ca'

    def __init__(self, host, user, pw, db='capublic'):
        self.engine = create_engine('mysql://%s:%s@%s/%s?charset=utf8' % (
                user, pw, host, db))
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def scrape_bills(self, chamber, year):
        if int(year) < 1989 or int(year) > dt.datetime.today().year:
            raise NoDataForYear(year)

        if int(year) % 2 != 1:
            raise NoDataForYear(year)

        if chamber == 'upper':
            measure_abbr = 'SB'
        else:
            measure_abbr = 'AB'
        
        year2 = str(int(year) + 1)
        session = "%s%s" % (year, year2)

        bills = self.session.query(Bill).filter_by(
            session_year=session).filter_by(
            measure_type=measure_abbr)

        for bill in bills:
            self.add_bill(chamber, session, bill.short_bill_id,
                          bill.versions[0].title)

if __name__ == '__main__':
    CASQLImporter('localhost', 'USER', 'PASSWORD').run()