from profiteer import common_f

class Holder (object):
    def __init__(self, l):
        super(Holder, self).__init__()
        self.list = l

class DataItem (object):
    def __init__(self, name, value):
        super(DataItem, self).__init__()
        self.name = name
        self.value = value

# Creates a fake cgi_form for testing purposes
def new_cgi_form(data):
    l = [DataItem(n, v) for n, v in data]
    
    common_f.cgi_form = Holder(l)
    
    return l

