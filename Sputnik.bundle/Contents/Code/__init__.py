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
API_SERIES = "http://r7.tv2.dk/api/sputnik/series.json"
API_SNEAKPREVIEWS = "http://r7.tv2.dk/api/sputnik/programs/sneakpreview.json"
API_LATESTPROGRAMS = "http://r7.tv2.dk/api/sputnik/programs/sort-latest/page-1.json"
API_CATEGORIES = "http://r7.tv2.dk/api/sputnik/categories.json"

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, L('Title'), ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    Plugin.AddViewGroup("MediaPreview", viewMode="MediaPreview", mediaType="items")
    Plugin.AddViewGroup("Showcase", viewMode="Showcase", mediaType="items")
    Plugin.AddViewGroup("Coverflow", viewMode="Coverflow", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)


def CreatePrefs():
    Prefs.SetDialogTitle('Sputnik account settings')
    Prefs.Add(id = 'username', type = 'text', default = None, label = 'Username')
    Prefs.Add(id = 'password', type = 'text', default = None, label = 'Password', option = 'hidden')

def MainMenu():
    dir = MediaContainer(viewGroup="List")
    dir.Append(Function(DirectoryItem(ListSeries, 'Series')))
    dir.Append(Function(DirectoryItem(ListCategories, 'Categories')))
    dir.Append(Function(DirectoryItem(ListLatestPrograms, 'Latest Programs')))
    dir.Append(Function(DirectoryItem(ListSneakpreviews, 'Sneakpreviews')))
    dir.Append(PrefsItem('Settings', 'Sputnik account settings', thumb = R(ICON)))
    return dir
    
def GetImage(entity):
    selected = R(ICON)
    
    for image in entity["media_images"]:
        current_width = 0
        if(image["media_image_type"]["code"] == "teaser"):
            for image_file in image["media_image_files"]:
                if(float(image_file["width"]) > current_width) and (float(image_file["width"]) > 130):
                    current_width = float(image_file["width"])
                    selected = image_file["location_uri"]
            if(selected != R(ICON)):
                break
        
        if(image["media_image_type"]["code"] == "16:9-thumb"):
            for image_file in image["media_image_files"]:
                if(float(image_file["width"]) > current_width):
                    current_width = float(image_file["width"])
                    selected = image_file["location_uri"]    
    
    return selected

def GetSubtitle(program):
    out = ""
    if(program["season"]):
        out += "Season " + program["season"]["title"]
        if(program["episode"]):
            out += " : "
        
    if(program["episode"]):
        out += "Episode "+program["episode"]
    
    return out
    
def ListSeries(sender):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    response = JSON.ObjectFromURL(API_SERIES, cacheTime=300);
    for series in response["series"]:
                        
        dir.Append(Function(DirectoryItem(
                ShowSeries,
                title   = series["code"],
                summary = series["description"],
                thumb   = GetImage(series)
            ), id = series["id"]))
    
    return dir

def ListCategories(sender):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    response = JSON.ObjectFromURL(API_CATEGORIES, cacheTime=300);
    for category in response["categories"]:
                        
        if(category["title"] != None):
            title = category["title"]
        else:
            title = category["code"]                
                        
        dir.Append(Function(DirectoryItem(
                ShowCategory,
                title   = title,
                summary = category["description"],
                thumb   = GetImage(category)
            ), id = category["id"]))
    
    return dir

def ListSneakpreviews(sender):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    response = JSON.ObjectFromURL(API_SNEAKPREVIEWS, cacheTime=300);
    for program in response["programs"]:
        
        title = ""
        if(program["series"]):
            title += program["series"]["code"]+" - "                
        title += program["title"]
                        
        dir.Append(Function(WebVideoItem(
                LoadProgram,
                title   = title,
                summary = program["description"],
                subtitle   = GetSubtitle(program),
                thumb   = GetImage(program)
            ), id = program["id"]))
            
    if(len(dir) == 0):
        return MessageContainer("Sneakpreviews", 'No programs found')
    
    return dir

def ListLatestPrograms(sender):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    response = JSON.ObjectFromURL(API_LATESTPROGRAMS, cacheTime=300);
    for program in response["programs"]:
        
        title = ""
        if(program["series"]):
            title += program["series"]["code"]+" - "                
        title += program["title"]
                        
        dir.Append(Function(WebVideoItem(
                LoadProgram,
                title   = title,
                summary = program["description"],
                subtitle   = GetSubtitle(program),
                thumb   = GetImage(program)
            ), id = program["id"]))
                
    return dir

def ShowSeries(sender, id):
    dir = MediaContainer(viewGroup="Coverflow", title2=sender.itemTitle)
    response = JSON.ObjectFromURL("http://r7.tv2.dk/api/sputnik/series/"+id+"/programs/sort-latest/page-1.json", cacheTime=300);
    for program in response["programs"]:
        dir.Append(Function(WebVideoItem(
                LoadProgram,
                title      = response["code"]+" - "+program["title"],
                summary    = program["description"],
                subtitle   = GetSubtitle(program),
                thumb     = GetImage(program)
            ), id = program["id"]))
    
    if(len(dir) == 0):
        return MessageContainer(response["code"], 'No programs found')
        
    return dir
    
def ShowCategory(sender, id):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    response = JSON.ObjectFromURL("http://r7.tv2.dk/api/sputnik/categories/"+id+".json", cacheTime=300);
    
    if(len(response["children"]) > 0):
        for category in response["children"]:
            if(category["title"] != None):
                title = category["title"]
            else:
                title = category["code"]                
                        
            dir.Append(Function(DirectoryItem(
                    ShowCategory,
                    title   = title,
                    summary = category["description"],
                    thumb   = GetImage(category)
            ), id = category["id"]))
    else:
        response_series = JSON.ObjectFromURL("http://r7.tv2.dk/api/sputnik/categories/"+id+"/series.json", cacheTime=300);
        if(len(response_series["series"]) > 0):
            dir.Append(Function(DirectoryItem(
                    ListCategorySeries,
                    title   = "Series ("+str(len(response_series["series"]))+")",
                    summary = "Show all series in category",
                    thumb   = R(ICON)
            ), content = response_series["series"]))
            
        response_programs = JSON.ObjectFromURL("http://r7.tv2.dk/api/sputnik/categories/"+id+"/programs/sort-latest/page-1.json", cacheTime=300);
        if(response_programs["total_programs"] > 0):
            dir.Append(Function(DirectoryItem(
                    ListCategoryPrograms,
                    title   = "Programs ("+response_programs["total_programs"]+")",
                    summary = "Show all programs in category",
                    thumb   = R(ICON)
            ), content = response_programs["program"]))
                
    return dir

def ListCategorySeries(sender, content):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    
    return dir
    
def ListCategoryPrograms(sender, content):
    return dir
    
def LoadProgram(sender, id):
    url = "http://sputnik-dyn.tv2.dk/player/simple/id/" + id;
    key = WebVideoItem(url).key
    return Redirect(key)
    
    
    
    
