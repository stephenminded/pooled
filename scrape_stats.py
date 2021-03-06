#!/usr/bin/env python
import os
import logging
import sys
from mechanize import Browser
from BeautifulSoup import BeautifulSoup

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
os.environ['PYTHONPATH'] = '/home/steve/django/testsite'

from pooled.models import *

logger = logging.getLogger("mechanize")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

def get_player(col):
    # Figure out which player we are dealing
    # with what position they place, and which
    # team they are on.
    links = col[0].findAll('a')
    player_name = links[0].string.strip()
    player_slug = links[0]['href'].strip('/').rsplit('/')[-1]
    team = links[1].string.strip()
    team_slug = links[1]['href'].strip('/').rsplit('/')[-1]
    pos = col[1].string.strip()
    
    p = Player.objects.filter(sportsnet=player_slug)
    if (p.count() == 0):
        t = Team.objects.filter(slug=team_slug)
        if (t.count() == 0):
            t = Team(name=team, slug=team_slug)
            t.save()
        else:
            t = t[0]
        p = Player(team=t, name=player_name, nhlcom=1, position=pos, sportsnet=player_slug)
        p.save()
    else:
        p=p[0]
    
    return p

def get_player_stats(soup):
    table = soup.findAll('table')[6]
    records = list()
    for tr in table.findAll('tr')[1:]:
        col = tr.findAll('td')
        player = get_player(col)
        
        gp = int(col[2].string.strip())
        g = int(col[3].string.strip())
        a = int(col[4].string.strip())
        pts = int(col[5].string.strip())
        plus_minus = int(col[7].string.strip())
        ppg = int(col[8].string.strip())
        ppa = int(col[10].string.strip())
        ppp = int(col[11].string.strip())
        shg = int(col[12].string.strip())
        gwg = int(col[13].string.strip())
        pim = int(col[14].string.strip())
        sh = int(col[15].string.strip())
        
        stat = PlayerStat(
            player=player,
            current=True,
            gp=gp,
            g=g,
            a=a,
            pts=pts,
            plus_minus=plus_minus,
            ppg=ppg,
            ppa=ppa,
            ppp=ppp,
            shg=shg,
            gwg=gwg,
            pim=pim,
            sh=sh)
        stat.save()
        
def get_goalie_stats(soup):
    table = soup.findAll('table')[5]
    records = list()
    for tr in table.findAll('tr')[1:]:
        col = tr.findAll('td')
        player = get_player(col)
        
        gp = int(col[2].string.strip())
        w = int(col[3].string.strip())
        l = int(col[4].string.strip())
        otl = int(col[5].string.strip())
        gaa = col[6].string.strip()
        save_pct = col[7].string.strip()
        so = int(col[8].string.strip())
        en = int(col[9].string.strip())
        ga = int(col[10].string.strip())
        sha = int(col[11].string.strip())
        starts = int(col[12].string.strip())
        
        stat = GoalieStat(
            player=player,
            current=True,
            gp=gp,
            w=w,
            l=l,
            otl=otl,
            gaa=gaa,
            save_pct=save_pct,
            so=so,
            en=en,
            ga=ga,
            sha=sha,
            starts=starts)
        stat.save()

def iterate_pages(mech, callback, limit=False):
    i = 0
    while True:
        response = mech.response()
        html = response.read()
        soup = BeautifulSoup(html)
        callback(soup)
        i+=1
        print "Processed page %d" % i
        if limit != False and limit>=i:
            break
        try:
            mech.follow_link(text_regex="Next page")
        except:
            print 'done.'
            break
        
def get_mechanized_browser(url):
    mech = Browser()
    mech.set_handle_robots(False)
    mech.open(url)
    assert mech.viewing_html()
    return mech

player_stats = get_mechanized_browser("http://www.sportsnet.ca/hockey/nhl/stats/skaters")
goalie_stats = get_mechanized_browser("http://www.sportsnet.ca/hockey/nhl/stats/goalies")
# we're updating the stats, so all the old stats are not current
PlayerStat.objects.all().update(current=False)
GoalieStat.objects.all().update(current=False)

iterate_pages(player_stats, get_player_stats, 1)
iterate_pages(goalie_stats, get_goalie_stats, 1)

updated = GoalieStat.objects.filter(current=True)
print 'Updated a total of %d goalies' % updated.count()
updated = PlayerStat.objects.filter(current=True)
print 'Updated a total of %d players' % updated.count()
