import re

import lxml.html
from fiftystates.scrape import NoDataForPeriod
from fiftystates.scrape.legislators import (LegislatorScraper, Legislator,
                                            Person)


class MALegislatorScraper(LegislatorScraper):
    state = 'ma'

    def scrape(self, chamber, term):
        if term != '186':
            # Data only available for current term
            raise NoDataForPeriod(term)

        if chamber == 'upper':
            chamber_type = 'Senate'
        else:
            chamber_type = 'House'

        url = "http://www.malegislature.gov/People/%s" % (chamber_type,)
        with self.urlopen(url) as page:
            root = lxml.html.fromstring(page)

            for member_url in root.xpath('//div[@class="container"]/a/@href'):
                member_url = "http://www.malegislature.gov"+member_url
                self.scrape_member(chamber, term, member_url)

    def scrape_member(self, chamber, term, member_url):
        with self.urlopen(member_url) as page:
            root = lxml.html.fromstring(page)
            root.make_links_absolute(member_url)
            photo_url = root.xpath('//div[@class="bioPicContainer"]/img/@src')[0]
            full_name = root.xpath('//div[@class="bioPicContainer"]/img/@alt')[0]

            name_parts = full_name.split(' ')
            first_name = last_name = middle_name = None
            if len(name_parts) == 2:
                first_name, last_name = name_parts
                middle_name = ''
            elif len(name_parts) == 3:
                first_name, middle_name, last_name = name_parts
            elif len(name_parts) > 3:
                first_name = name_parts[0]
                middle_name = name_parts[1]
                last_name = name_parts[2]

            district = root.xpath('//div[@id="District"]//div[@class="widgetContent"]')
            if len(district):
                district = district[0].text.strip()
                if len(district.split(' - ')) > 1:
                    district = district.split(' - ')[0]
                elif len(district.split('. ')) > 1:
                    district = district.split('. ')[0]
                else:
                    district = district[0:32]
            else:
                district = 'NotFound'

            party = root.xpath('//div[@class="bioDescription"]/div')[0].text.strip().split(',')[0]
            if party == 'Democrat':
                party = 'Democratic'
            elif party == 'Republican':
                party = 'Republican'

            leg = Legislator(term, chamber, district, full_name,
                                 party=party, photo_url=photo_url,
                                 first_name=first_name, middle_name=middle_name,
                                 last_name=last_name)

            leg.add_source(member_url)

            comm_div = root.xpath('//div[@id="Column5"]//div[@class="widgetContent"]')
            if len(comm_div):
                comm_div = comm_div[0]
                for li in comm_div.xpath('/ul/li'):
                    role = li.xpath('text()').strip()
                    comm = li.xpath('/a/text()').strip()[0].strip(',')
                    if role == 'Member':
                        role = 'committee member'
                    leg.add_role(role, term, chamber=chamber,
                                     committee=comm)

            self.save_legislator(leg)
