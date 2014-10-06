'''
A client for accessing the OU CORE API
http://core-project.kmi.open.ac.uk/api-doc/
'''

from portality.core import app

    
class core(object):
    def __init__(self, url=False, apikey=False):
        self.url = url
        self.apikey = apikey
        if not self.url:
            try:
                self.url = app.config['PROCESSORS']['core']['url'].rstrip('/') + '/'
                if not self.apikey:
                    self.apikey = app.config['PROCESSORS']['core']['url']
            except:
                return None
        self.response = None
        self.data = None

    def search(self,value):
        result = {}
        try:
            addr = self.url + value
            addr += "?format=json&api_key=" + self.apikey
            self.response = requests.get(addr)
            self.data = r.json()
    
            if 'ListRecords' in self.data and len(self.data['ListRecords']) != 0:
                record = self.data['ListRecords'][0]['record']['metadata']['oai_dc:dc']
                result['url'] = record["dc:source"]
                result['title'] = record["dc:title"]
                result['description'] = record["dc:description"]
            return result
        except:
            return result



