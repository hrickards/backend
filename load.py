
import json, requests, re, uuid

es = "http://localhost:9200"
index = "oabutton"
indextype = "record"

addr = es + "/" + index + "/" + indextype

infile = "oa.json"

recs = json.load(open(infile,"r"))


counter = 0
for rec in recs:

    # this should probably create bibjson, but it's fine like this for now
    # see below for an example oabutton legacy record
    p = rec["description"]
    p = p.replace("\r","")
    ps = p.split("\n")
    for pt in ps:
        if pt.lower().startswith("title"):
            r = re.compile(re.escape('title'), re.IGNORECASE)
            pt = r.sub('',pt)
            pt = pt.lstrip(": ")
            rec["title"] = pt
        if pt.lower().startswith("authors"):
            r = re.compile(re.escape('authors'), re.IGNORECASE)
            pt = r.sub('',pt)
            pt = pt.lstrip(": ")
            rec["author"] = [i.strip() for i in pt.split(",")]
        if pt.lower().startswith("author"):
            r = re.compile(re.escape('author'), re.IGNORECASE)
            pt = r.sub('',pt)
            pt = pt.lstrip(": ")
            rec["author"] = [i.strip() for i in pt.split(",")]
        if pt.lower().startswith("auther"):
            r = re.compile(re.escape('auther'), re.IGNORECASE)
            pt = r.sub('',pt)
            pt = pt.lstrip(": ")
            rec["author"] = [i.strip() for i in pt.split(",")]
        if pt.lower().startswith("journal"):
            r = re.compile(re.escape('journal'), re.IGNORECASE)
            pt = r.sub('',pt)
            pt = pt.lstrip(": ")
            rec["journal"] = pt
        if pt.lower().startswith("date"):
            r = re.compile(re.escape('date'), re.IGNORECASE)
            pt = r.sub('',pt)
            pt = pt.lstrip(": ")
            rec["date"] = pt
            
    rec['id'] = uuid.uuid4().hex

    r = requests.post(addr + "/" + rec['id'], data=json.dumps(rec))
    if r.status_code == 201: counter += 1


print("Read " + str(len(recs)) + " records from file " + infile + " and saved " + str(counter) + " to " + addr)



'''

{
    "story": "Re-checking some work for my dissertation", 
    "doi": "10.1016/j.neurobiolaging.2012.12.011", 
    "coords": {"lat": 52.5, "lng": 13.4}, 
    "user_profession": "Student", 
    "url": "http://www.sciencedirect.com/science/article/pii/S0197458012006422", 
    "accessed": "Nov 18, 2013", 
    "user_name": "Joseph McArthur", 
    "description": "Title: Fractalkine overexpression suppresses tau pathology in a mouse model of tauopathy\r\nAuthors: Kevin R. Nash, Daniel C. Lee, Jerry B. Hunt, Josh M. Morganti, Maj-Linda Selenica, Peter Moran, Patrick Reid, Milene Brownlow, Clement Guang-Yu Yang, Miloni Savalia, Carmelina Gemma, Paula C. Bickford, Marcia N. Gordon, David Morgan\r\nJournal: Neurobiology of Aging\r\nDate: 2013-6"
}

Author field inside description has been seen with at least Auther and author

'''
