# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
import re

####################################################################################################

VIDEO_PREFIX = "/video/sputnik"
NAME = L('Title')
ART           = 'backdrop.png'
ICON          = 'icon.png'

NAMESPACES = {"media":"http://search.yahoo.com/mrss/"}
RSS_SERIES = "http://sputnik.tv2.dk/rss.xml"

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('Title'), ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)


def CreatePrefs():
    Prefs.SetDialogTitle('Sputnik konto indstillinger')
    Prefs.Add(id = 'username', type = 'text', default = None, label = 'Brugernavn')
    Prefs.Add(id = 'password', type = 'text', default = None, label = 'Kodeord', option = 'hidden')

def MainMenu():
    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(ListSeries, 'Serier')))
    dir.Append(PrefsItem('Indstillinger', 'Sputnik konto indstillinger', thumb = R(ICON)))
    return dir
    
def ListSeries(sender):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    for series in XML.ElementFromURL(RSS_SERIES, errors="ignore", cacheTime=300).xpath('//item'):    
        
        thumbs = series.xpath(".//media:thumbnail", namespaces=NAMESPACES)
        if(len(thumbs) > 0):
            thumb = thumbs[0].get('url')
        else:
            thumb = R(ICON)
        
        dir.Append(Function(DirectoryItem(
                ShowSeries,
                title       = series.find('title').text,
                summary     = series.find('description').text,
                thumb       = thumb
            ), rss_url = series.find('link').text))
    
    return dir

def ShowSeries(sender, rss_url):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    feed = XML.ElementFromURL(rss_url, errors="ignore", cacheTime=300)
    for program in feed.xpath('//item'):
        
        thumbs = program.xpath(".//media:thumbnail", namespaces=NAMESPACES)
        if(len(thumbs) > 0):
            thumb = thumbs[0].get('url')
        else:
            thumb = R(ICON)
        
        path = program.xpath(".//media:player", namespaces=NAMESPACES)
        if(len(path) == 0):
            continue
            
        m = re.search('http:\/\/sputnik.*.tv2.dk\/play\/([\d]+)', path[0].get('url'))
        
        dir.Append(Function(WebVideoItem(
                LoadProgram,
                title       = program.find('title').text,
                summary    = program.find('description').text,
                thumb     = thumb
            ), programid = m.group(1) ))
    
    if(len(dir) == 0):
        return MessageContainer(feed.xpath('//title')[0].text, 'Ingen programmer fundet')
        
    return dir
    
def LoadProgram(sender, programid):
    username = Prefs.Get('username')
    password = Prefs.Get('password')
    
    ticketurl = "http://sputnik.tv2.dk/player/external/?username="+username+"&password="+password+"&object="+programid
    if (Dict.Get('apptoken') != None):
        ticketurl = ticketurl + "&apptoken=" + Dict.Get('apptoken')
    
    ticket = JSON.ObjectFromURL(ticketurl)
    Dict.Set('apptoken', ticket['apptoken'])
    
    if(ticket['ticket'] == 0):
        ticket['ticket'] = "none"
    
    url = "http://sputnik.tv2.dk/player/boxee/object/" + programid + "?ticket=" + ticket['ticket']
    key = WebVideoItem(url).key.replace('.','%2E')
    return Redirect(key)