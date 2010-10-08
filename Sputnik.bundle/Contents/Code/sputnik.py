from PMS import *

class Query:
    def AccessProfile(self):
        username = Prefs.Get('username')
        password = Prefs.Get('password')
        if username == None or password == None:
            return Profile()
        HTTP.SetPassword('http://r7.tv2.dk/api/sputnik/access/profile.json', username=username, password=password)
        result = HTTP.Request('http://r7.tv2.dk/api/sputnik/access/profile.json', cacheTime=300);
        return Profile(JSON.ObjectFromString(result))

    def Programs(self, sort="latest", page="1"):
        data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/programs/sort-'+sort+'/page-'+page+'.json', cacheTime=300)
        programs = []
        for program in data["programs"]:
            programs.append(Program(program))

        data["programs"] = programs
        return data
    
    def ProgramsSneakpreview(self):
        data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/programs/sneakpreview.json', cacheTime=300)
        programs = []
        for program in data["programs"]:
            programs.append(Program(program))

        data["programs"] = programs
        return data

    def Series(self):
        data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/series.json', cacheTime=300)
        series = []
        for serie in data["series"]:
            series.append(Series(serie))

        data["series"] = series
        return data

    def SeriesPrograms(self, id, sort="latest", page="1"):
        data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/series/'+id+'/programs/sort-'+sort+'/page-'+page+'.json', cacheTime=300)
        series = Series(data)
        programs = []
        for program in data["programs"]:
            program["series"] = series
            programs.append(Program(program))

        data["programs"] = programs
        return data

    def Categories(self, id = None):
        if id == None:
            data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/categories.json', cacheTime=300)
        else:
            data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/categories/'+str(id)+'.json', cacheTime=300)
            data["categories"] = data["children"]
        
        categories = []
        for category in data["categories"]:
            categories.append(Category(category))
        
        data['categories'] = categories
        return data

    def CategoryContent(self, id):
        data = {}
        data["series"]      = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/categories/'+str(id)+'/series.json', cacheTime=300)
        data["programs"]    = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/categories/'+str(id)+'/programs/sort-latest/page-1.json', cacheTime=300)
    
        items = {}
        for serie in data["series"]["series"]:
            items[serie["code"]+str(serie["id"])] = Series(serie)
        for program in data["programs"]["programs"]:
            if program["series"] == None:
                items[program["title"]+str(program["id"])] = Program(program)
        
        pages = int(data["programs"]["total_pages"])
        if pages > 1:
            for i in range(2, pages + 1):
                response = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/categories/'+str(id)+'/programs/sort-latest/page-'+str(i)+'.json', cacheTime=300)
                for program in response["programs"]:
                    if program["series"] == None:
                        items[program["title"]+str(program["id"])] = Program(program)

        aitems = []
        for key in sorted(items):
            aitems.append(items[key])
        return {"items":aitems}

    def Search(self, query):
        data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/search.json?query='+query, cacheTime=300);
        if data["valid"] != True:
            return False
        programs = []
        for program in data["programs"]:
            programs.append(Program(program))
        series = []
        for serie in data["series"]:
            series.append(Series(serie))
        data["programs"] = programs
        data["series"] = series
        return data

    def LiveChannels(self):
        data = JSON.ObjectFromURL('http://r7.tv2.dk/api/sputnik/placeholder/687/content.json', cacheTime=300)
        programs = []
        for entity in data["entities"]:
            if entity['r7_type'] == "R7_Entity_Broadcast":
                entity["episode"] = None
                entity["season"] = None
                programs.append(Program(entity))
        return programs

class Profile:
    groups      = []
    singles     = []

    def __init__(self, data=None):
        if data != None:
            for service in data["services"]["subscriptions"]:
                for group in service["commercial_groups"]:
                    self.groups.append(group["code"])

            for single in data["services"]["single"]:
                self.singles.append(single['program']['id'])

class Program:
    id          = None
    title       = None
    fulltitle   = None
    subtitle    = None
    description = None
    series      = None
    season      = None
    episode     = None
    category    = None
    image       = None
    nocharge    = False
    group       = None

    def __init__(self, data=None):
        self.series         = Series()
        self.category       = Category()
        self.season         = Season()
        self.image          = Image()

        if isinstance(data, dict):
            self.id             = data["id"]
            self.title          = data["title"]
            self.fulltitle      = data["title"]
            self.description    = data["description"]
            self.episode        = data["episode"]
            self.nocharge       = data["nocharge"]
            
            if "commercial_group" in data:
                if isinstance(data["commercial_group"], dict):
                    self.group = data["commercial_group"]["code"]

            if "series" in data:
                if isinstance(data["series"], dict) or data["series"] == None:
                    self.series = Series(data["series"])
                else:
                    self.series = data["series"]

            if "category" in data:
                if isinstance(data["category"], dict) or data["category"] == None:
                    self.category = Category(data["category"])
                else:
                    self.category = data["category"]
            
            if "season" in data:
                self.season         = Season(data["season"])
            
            if "media_images" in data:
                self.image          = Image(data["media_images"])
            
            if self.season.title != None:
                self.subtitle = "Season " + self.season.title

            if self.episode != None:
                if self.season.title != None:
                    self.subtitle += " : Episode " + self.episode
                else:
                    self.subtitle = "Episode " + self.episode

            if self.series.title != None:
                self.fulltitle = self.series.title + " : " + self.title

class Image:
    url = None

    def __init__(self, data=None):
        self.url = R('icon.png')
        
        if data != None:
            for image in data:
                current_width = 0
                if(image["media_image_type"]["code"] == "teaser"):
                    for image_file in image["media_image_files"]:
                        if(float(image_file["width"]) > current_width) and (float(image_file["width"]) > 130):
                            current_width = float(image_file["width"])
                            self.url = image_file["location_uri"]
                    if(self.url != R('icon.png')):
                        break
                
                if(image["media_image_type"]["code"] == "poster"):
                    for image_file in image["media_image_files"]:
                        if(float(image_file["width"]) > current_width):
                            current_width = float(image_file["width"])
                            self.url = image_file["location_uri"]
                    if(self.url != R('icon.png')):
                        break

                if(image["media_image_type"]["code"] == "16:9-thumb"):
                    for image_file in image["media_image_files"]:
                        if(float(image_file["width"]) > current_width):
                            current_width = float(image_file["width"])
                            self.url = image_file["location_uri"]    

class Series:
    id          = None
    title       = None
    subtitle    = None
    description = None
    category    = None
    image       = None

    def __init__(self, data=None):
        self.category   = Category()
        self.image      = Image()
        
        if isinstance(data, dict):
            self.id             = data["id"]
            self.title          = data["code"]
            self.description    = data["description"]
                
            if "category" in data:
                if isinstance(data["category"], dict) or data["category"] == None:
                    self.category = Category(data["category"])
                else:
                    self.category = data["category"]

            if self.category.title != None:
                self.subtitle = self.category.title

            if "media_images" in data:
                self.image = Image(data["media_images"])

class Category:
    id          = None
    title       = None
    subtitle    = None
    description = None
    parent      = None
    children    = []
    image       = None

    def __init__(self, data=None):
        self.image      = Image()

        if isinstance(data, dict):
            self.id             = data["id"]
            self.title          = data["code"]
            self.description    = data["description"]

            if data["title"] != None:
                self.title  = data["title"]

            if "parent" in data:
                if isinstance(data["parent"], dict) or data["parent"] == None:
                    self.parent = Category(data["parent"])
                else:
                    self.parent = data["parent"]
            
            if "media_images" in data:
                self.image = Image(data["media_images"])

class Season:
    id      = None
    title   = None

    def __init__(self, data=None):
        if isinstance(data, dict):
            self.id = data["id"]
            self.title = data["title"]

