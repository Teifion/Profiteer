import random
from profiteer import common_f, config
from collections import OrderedDict
import functools
import os
from http import cookies

data = {
    'double_click_id_cache':    0,
    'uid':                      str(random.random())[3:9]
}

onload = """
<script type="text/javascript" charset="utf-8">
    $(document).ready(function() {
        %s
    });
</script>"""

def html_escape(content):
    content.replace("&", "&amp;")
    
    return content

def js_name(text):
    return text.replace("'", "\\'").replace("(", "").replace(")", "")

# Used to handle a 404 page
class HTTP404 (object):
    page_data = {
        "Template": "admin",
        'Title':    "HTTP 404",
        "Padding":  5,
    }
    
    def __init__(self, mode):
        super(HTTP404, self).__init__()
        self.mode = mode
    
    def main(self, *args, **kwargs):
        return "<br /><div class='error'>404 for {}</div>".format(self.mode)

# Output a HTML checkbox
def check_box(name, checked=False, custom_id=''):
    output = ['<input type="checkbox" name="%s" value="True"' % name]
    
    if checked:
        output.append('checked="checked"')
    
    if custom_id != '': output.append('id="%s"' % custom_id)
    else:               output.append('id="%s"' % name)
    
    output.append('/>')
    return " ".join(output)

# Output a HTML textbox
def text_box(name, text='', size=15, tabIndex=-1, onchange='', custom_id='<>', style="", warn_on=None, disabled=False):
    if custom_id == "<>": custom_id = name
    
    if warn_on != None:
        if warn_on(text):
            style = "%sbackground-color:#FAA;border:2px solid #A00;" % style
    
    # No size?
    size = "" if size == -1 else 'size="%s" ' % size
    disabled = " disabled='disabled'" if disabled == True else ""

    # If no cols, width = 100%
    if size == "":
        style = style + "width:100%;"
    
    output = ['<input type="text" name="%s" %svalue="%s" onchange="%s" id="%s" style="%s"%s' % (name, size, text, onchange, custom_id, style, disabled)]
    
    if tabIndex > 0:
        output.append(' tabIndex="%s"' % tabIndex)
    
    output.append(" />")
    return "".join(output)

def textarea(name, text='', rows=6, cols=30, tabIndex=-1, onchange='', custom_id='<>', style="", warn_on=None):
    if custom_id == "<>": custom_id = name
    
    if warn_on != None:
        if warn_on(text):
            style = "%sbackground-color:#FAA;border:2px solid #A00;" % style
    
    # No cols?
    cols = "" if cols==-1 else 'cols="%s" ' % cols
    
    # If no cols, width = 100%
    if cols == "":
        style = style + "width:100%;"
    
    output = ['<textarea name="%s" rows="%s" %sonchange="%s" id="%s" style="%s"' % (name, rows, cols, onchange, custom_id, style)]
    
    if tabIndex > 0: output.append(' tabIndex="%s" ' % tabIndex)
    
    output.append(">%s</textarea>" % text)
    return "".join(output)

def _sort_elements(sequence, element_property="name"):
    """Sorts the elements of a dictionary or list while preserving their numerical order"""
    new_sequence = OrderedDict()
    
    if type(sequence) == set:
        sequence = list(sequence)
    
    if type(sequence) in (list, tuple):
        true_sequence = list(sequence)
        ordered_sequence = list(sequence)
        ordered_sequence.sort()
        
        for i in ordered_sequence:
            new_sequence[true_sequence.index(i)] = i
    
    elif type(sequence) in (dict, OrderedDict):
        try:
            reverse_dict = {v:k for k, v in sequence.items()}
            ordered_sequence = [v for k, v in sequence.items()]
            ordered_sequence.sort()

            for i in ordered_sequence:
                new_sequence[reverse_dict[i]] = i
        
        except TypeError as e:
            # We need to use the element_property
            reverse_dict = {v.__dict__[element_property]:k for k, v in sequence.items()}
            ordered_sequence = [v.__dict__[element_property] for k, v in sequence.items()]
            ordered_sequence.sort()
        
            for i in ordered_sequence:
                new_sequence[reverse_dict[i]] = i
        
        except Exception as e:
            raise
        
    else:
        raise Exception("Cannot sort type: %s" % type(sequence))
    
    return new_sequence

def option_box(name, elements, selected="", tab_index = -1, custom_id="<>", onchange="", style="", disabled=[], insert_dud=False, element_property="name", css_class="", sort=True):
    disabled_count = 0
    
    output = ['<select name="{name}" style="{style}" {custom_id}onchange="{onchange}" class="{css_class}"'.format(
        name = name,
        custom_id = ('id="%s" ' % custom_id if custom_id != "<>" else ""),
        onchange = onchange,
        style = style,
        css_class = css_class,
    )]
    
    if tab_index > 0:
        output.append('tabIndex="{}"'.format(tab_index))
    
    output.append('>')
    
    if insert_dud != False:
        output.append('<option value="">{}</option>'.format(insert_dud))
    
    # Sort?
    if sort:
        elements = _sort_elements(elements, element_property)
    
    # Is it a list/tuple or dictionary
    if type(elements) in (list, tuple):
        iterator = enumerate(elements)
    else:
        iterator = elements.items()
    
    for k, v in iterator:
        if type(v) not in (str, int):
            v = v.__dict__[element_property]
        
        is_selected = ""
        if selected == k:
            is_selected = 'selected="selected"'
        
        if k in disabled:
            disabled_count += 1
            output.append('<option value="disabled_{}" disabled="disabled">&nbsp;</option>'.format(disabled_count))
            continue
        
        output.append('<option value="{}" {}>{}</option>'.format(k, is_selected, v))
    
    output.append('</select>')
    return "".join(output)


def live_option_box(elements, table, field, where_id, value, tab_index = -1, style="", disabled=[], element_property="name", sort=True):
    data['double_click_id_cache'] += 1
    elem_id = "live_option_%s_%s_%s" % (field, data['double_click_id_cache'], data['uid'])
    
    # If we can get the selected to line up right we've got ourselves a much shorter function
    # 
    # onchange = """$('#ajax_target').load('web.py', {{'mode':'edit_one_field','table':'{table}','field':'{field}','where':'{where}','value':$('#{elem}').val(),'silent':'True'}});""".format(
    #         table = table,
    #         field = field,
    #         where = "id=%d" % where_id,
    #         elem = elem_id,
    #     ),

    # return option_box(
    #     name="dud_name",
    #     elements=elements,
    #     selected="",
    #     tab_index = tab_index,
    #     custom_id=elem_id,
    #     onchange=onchange,
    #     style=style,
    #     disabled=disabled,
    #     insert_dud=False,
    #     element_property=element_property,
    #     sort=sort
    # )
    
    disabled_count = 0
    data['double_click_id_cache'] += 1
    
    
    output = ['<select id="{elem_id}" style="{style}" onchange="{change}"'.format(
        elem_id = elem_id,
        style = style,
        change = """$('#ajax_target').load('web.py', {{'mode':'edit_one_field','table':'{table}','field':'{field}','where':'{where}','value':$('#{elem}').val(),'silent':'True'}});""".format(
            table = table,
            field = field,
            where = "id=%d" % where_id,
            elem = elem_id,
        ),
    )]
    
    if tab_index > 0:
        output.append('tabIndex="{}"'.format(tab_index))
    
    output.append('>')
    
    # Sort?
    if sort:
        elements = _sort_elements(elements)
    
    for k, v in elements.items():
        if type(v) not in (str, int):
            v = v.__dict__[element_property]
        
        is_selected = ""
        if value == k:
            is_selected = "selected='selected'"
        
        if k in disabled:
            disabled_count += 1
            output.append('<option value="disabled_{}" disabled="disabled">&nbsp;</option>'.format(disabled_count))
            continue
        
        output.append('<option value="{}" {}>{}</option>'.format(k, is_selected, v))
    
    output.append('</select>')
    return "".join(output)

# It didn't work quite as hoped but I don't want to discard the code
# def doubleclick_option_box(elements, table, field, where_id, value, label_style="", disabled=[], element_property="name", sort=True):
#     return doubleclick_option_box_full(elements, table, field, "id=%d" % int(where_id), value, label_style, disabled, element_property, sort)
# 
# def doubleclick_option_box_full(elements, table, field, where_field, value, label_style="", disabled=[], element_property="name", sort=True):
#     disabled_count = 0
#     data['double_click_id_cache'] += 1
#     
#     elem_id = "live_option_%s_%s_%s" % (field, data['double_click_id_cache'], data['uid'])
#     
#     element_string = []
#     
#     # Sort?
#     if sort:
#         elements = _sort_elements(elements)
#     
#     # Is it a list/tuple or dictionary
#     if type(elements) in (list, tuple):
#         iterator = enumerate(elements)
#     else:
#         iterator = elements.items()
#     
#     for k, v in iterator:
#         if type(v) != str:
#             v = v.__dict__[element_property]
#         
#         is_selected = ""
#         if value == k:
#             is_selected = "selected='selected'"
#         
#         if k in disabled:
#             disabled_count += 1
#             element_string.append('<option value="disabled_{}" disabled="disabled">&nbsp;</option>'.format(disabled_count))
#             continue
#         
#         element_string.append('<option value="{}" {}>{}</option>'.format(k, is_selected, v))
#     
#     return """<span style="%(label_style)s" id="%(label)s" ondblclick="$('#%(input)s').val($('#%(label)s').text()); $('#%(label)s').hide(); $('#%(input)s').show(); $('#%(input)s').select();">%(value)s</span><select style="display:none; margin:-2px;" name="value" id="%(input)s" onblur="$('#%(label)s').load('web.py', {'mode':'edit_one_field','table':'%(table)s','field':'%(field)s','where':'%(where)s','value':$('#%(input)s').val()}, function () {$('#%(label)s').show(); $('#%(input)s').hide();});">%(element_string)s</select>""" % {
#     "table": table,
#     "field": field,
#     "where": where_field,
#     "value": elements[value],
#     "label_style": label_style,
#     "element_string":   "".join(element_string),
#     
#     "label": "label_%s_%s_%s" % (field, data['double_click_id_cache'], data['uid']),
#     "input": "input_%s_%s_%s" % (field, data['double_click_id_cache'], data['uid']),
#     }
#     
#     return "".join(output)

def doubleclick_text(table, field, where_id, value, label_style="", size=10):
    return doubleclick_text_full(table, field, "id=%d" % int(where_id), value, label_style, size)

def doubleclick_text_full(table, field, where_field, value, label_style="", size=10):
    """Creates a label that when double clicked turns into a textbox, when the textbox loses focus, it saves itself"""
    data['double_click_id_cache'] += 1
    
    # If no value is sent we want something to click on
    if value == "":
        value = "&nbsp;&nbsp;&nbsp;"
    
    return """<span style="%(label_style)s" id="%(label)s" ondblclick="$('#%(input)s').val($('#%(label)s').text()); $('#%(label)s').hide(); $('#%(input)s').show(); $('#%(input)s').select();">%(value)s</span><input style="display:none; margin:-2px;" type="text" name="value" id="%(input)s" size="%(size)s" value="" onblur="$('#%(label)s').load('web.py', {'mode':'edit_one_field','table':'%(table)s','field':'%(field)s','where':'%(where)s','value':$('#%(input)s').val()}, function () {$('#%(label)s').show(); $('#%(input)s').hide();});" />""" % {
    "table": table,
    "field": field,
    "where": where_field,
    "value": value,
    "label_style": label_style,
    "size": size,
    
    "label": "label_%s_%s_%s" % (field, data['double_click_id_cache'], data['uid']),
    "input": "input_%s_%s_%s" % (field, data['double_click_id_cache'], data['uid']),
    }

# Cookies are loaded and set automatically by web.py, to alter them simply use the below functions
cookies = cookies.SimpleCookie()
cookies.load(os.environ.get('HTTP_COOKIE', ''))

def set_cookie(name, value):
    cookies[name] = value

def delete_cookie(name):
    del(cookies[name])

def get_cookie(name, default=None):
    if name in cookies:
        return cookies[name].value
    else:
        return default
