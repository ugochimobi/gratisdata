#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017 emijrp <emijrp@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import re
import time

import pwb
import pywikibot
from wikidatafun import *

def getQueryCount(p='', q=''):
    if p and p.startswith('P') and \
       q and q.startswith('Q'):
        try:
            url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql?query=SELECT%20%28COUNT%28%3Fitem%29%20AS%20%3Fcount%29%20%23%20%3FitemLabel%0AWHERE%20{%0A%20%20%3Fitem%20wdt%3A'+p+'%2Fwdt%3AP279*%20wd%3A'+q+'.%0A%20%20SERVICE%20wikibase%3Alabel%20{%20bd%3AserviceParam%20wikibase%3Alanguage%20%22en%22%20}%0A}%0A'
            url = '%s&format=json' % (url)
            sparql = getURL(url=url)
            json1 = loadSPARQL(sparql=sparql)
            return json1['results']['bindings'][0]['count']['value']
        except:
            return ''
    return ''

def main():
    site = pywikibot.Site('en', 'wikipedia')
    ahk = pywikibot.Page(site, 'User:Emijrp/All Human Knowledge')
    ahktext = ahk.text
    ahknewtext = ahk.text
    
    #update inline stuff
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    wpenstatsurl = 'https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json'
    jsonwpen = json.loads(getURL(url=wpenstatsurl))
    wpenarticles = jsonwpen['query']['statistics']['articles']
    wdstatsurl = 'https://www.wikidata.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json'
    jsonwd = json.loads(getURL(url=wdstatsurl))
    wdarticles = jsonwd['query']['statistics']['articles']
    wpenwdstats = "<!-- wpenwdstats -->As of {{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}, [[English Wikipedia]] has {{formatnum:%s}} articles<ref>{{cite web | url=https://en.wikipedia.org/wiki/Special:Statistics | title=Special:Statistics | publisher=English Wikipedia | date=%s | accessdate=%s | quote=Content pages: {{formatnum:%s}}}}</ref> and [[Wikidata]] includes {{formatnum:%s}} items.<ref>{{cite web|url=https://www.wikidata.org/wiki/Special:Statistics | title=Special:Statistics | publisher=Wikidata | date=%s | accessdate=%s | quote=Content pages: {{formatnum:%s}}}}</ref><!-- /wpenwdstats -->" % (wpenarticles, today, today, wpenarticles, wdarticles, today, today, wdarticles)
    ahknewtext = re.sub(r'<!-- wpenwdstats -->.*?<!-- /wpenwdstats -->', wpenwdstats, ahknewtext)
    
    #update tables
    lines = ahknewtext.splitlines()
    summarydic = {}
    sections = []
    newlines = []
    newtotalwikidata = 0
    newtotalestimate = 0
    sectiontitle = ''
    sectionlevel = 0
    sectionparent = ''
    row_r = r'({{User:Emijrp/AHKrow\|(P\d+?)=([^\|\}]*?)\|wikidata=(\d*?)\|estimate=(\d*?)}})'
    rowtotal_r = r'({{User:Emijrp/AHKrowtotal\|wikidata=(\d*?)\|estimate=(\d*?)}})'
    for line in lines:
        newline = line
        
        if line.startswith('=') and line.endswith('='):
            sectionlevel = len(line.split(' ')[0])
            sectiontitle = line.replace('=', ' ').strip()
            if sectionlevel == 1:
                sectionparent = sectiontitle
        
        #update row
        if re.search(row_r, newline):
            m = re.findall(row_r, newline)
            for i in m:
                row, p, q, wikidata, estimate = i
                newwikidata = getQueryCount(p=p, q=q)
                newrow = row.replace('wikidata=%s|' % (wikidata), 'wikidata=%s|' % (newwikidata))
                newline = newline.replace(row, newrow)
                newtotalwikidata += newwikidata and int(newwikidata) or 0
                newtotalestimate += estimate and int(estimate) or (newwikidata and int(newwikidata) or 0)
        
        #update row total
        m = re.findall(rowtotal_r, newline)
        for i in m:
            totalrow, totalwikidata, totalestimate = i
            newtotalrow = totalrow
            newtotalrow = newtotalrow.replace('wikidata=%s|' % (totalwikidata), 'wikidata=%s|' % (newtotalwikidata))
            newtotalrow = newtotalrow.replace('estimate=%s}}' % (totalestimate), 'estimate=%s}}' % (newtotalestimate))
            newline = newline.replace(totalrow, newtotalrow)
            sections.append([sectiontitle, sectionlevel])
            summarydic[sectiontitle] = { 'parent': sectionparent, 'wikidata': newtotalwikidata, 'estimate': newtotalestimate }
            #reset
            newtotalwikidata = 0
            newtotalestimate = 0
        
        newlines.append(newline)
    ahknewtext = '\n'.join(newlines)
    
    #update summary
    summaryrows = []
    summarytotalwikidata = 0
    summarytotalestimate = 0
    for sectiontitle, sectionlevel in sections:
        if sectionlevel == 1:
            rowspan = 0
            for x, y in summarydic.items():
                if y['parent'] == sectiontitle:
                    rowspan += 1
            if rowspan >= 1:
                summaryrow = """| rowspan=%s | [[#%s|%s]]
|-""" % (rowspan, sectiontitle, sectiontitle)
        elif sectionlevel > 1:
            summaryrow = """| <li>[[#%s|%s]]
{{User:Emijrp/AHKsummaryrow|wikidata=%s|estimate=%s}}
|-""" % (sectiontitle, sectiontitle, summarydic[sectiontitle]['wikidata'], summarydic[sectiontitle]['estimate'])
            summarytotalwikidata += summarydic[sectiontitle]['wikidata']
            summarytotalestimate += summarydic[sectiontitle]['estimate']
        summaryrows.append(summaryrow)
    summarytotal = "{{User:Emijrp/AHKsummarytotal|wikidata=%s|estimate=%s}}" % (summarytotalwikidata, summarytotalestimate)
    summary = """<!-- summary -->{| class="wikitable sortable plainlinks"
! Topic !! Subtopic !! Wikidata !! Estimate
|-
%s
%s
|}<!-- /summary -->""" % ('\n'.join(summaryrows), summarytotal)
    ahknewtext = re.sub(r'<!-- summary -->.*?<!-- /summary -->', summary, ahknewtext)
    
    if ahknewtext and ahktext != ahknewtext:
        #pywikibot.showDiff(ahktext, ahknewtext)
        ahk.text = ahknewtext
        ahk.save('BOT - Updating The Catalogue of Catalogues')
    
if __name__ == '__main__':
    main()
