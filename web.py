# First we try importing the error printer
try:
    from profiteer import error
except Exception as e:
    raise
    print("Content-type: text/html; charset=utf-8")
    print("")
    print("Critical error importing error reporting module.<br><br>" + str(e))
    exit()

# Now we try importing everything else
try:
    from profiteer import database_f, common_f, html_f, cli_f
    import sys
    import time
    import imp
    import re
    
    # We import data so it will add to the pages.page_dict
    import data
    
    from profiteer import html_f
    from profiteer.gui import pages
except Exception as e:
    print(error.html_render(context=1, headers=False))
    raise

def _print_ignoring_error(text, test_mode=False):
    """Used to print out problematic unicode characters in the text as
    bright red and bold asterisks to help narrow down which ones they are"""
    
    text = re.sub(r"""[^a-zA-Z0-9!  *$@?_#\-'"+<>()\[\]:=,.;/&\\{}%\n]""", "<strong style='color:#F00;'>*</strong>", text)
    
    if test_mode:
        return text
    
    print(text)

def de_unicode(text):
    """Takes unicode and converts it into HTML entities"""
    
    text = text.replace("’", "&rsquo;")
    text = text.replace("‘", "&lsquo;")
    text = text.replace("“", "&ldquo;")
    text = text.replace("”", "&rdquo;")
    
    return text

page_dict = pages.page_dict

def import_page(page_name, handle_exception=True):
    """This is the main firing function of the admin GUI, it loads the
    page that we'll be using."""
    
    if page_name not in page_dict:
        the_page = html_f.HTTP404(page_name)
    else:
        try:
            path = page_dict[page_name][0], [
                page_dict[page_name][1],
                sys.path[0] + "/" + page_dict[page_name][1],
            ]
            find = imp.find_module(*path)
            the_page = imp.load_module("the_page", *find)
            find[0].close()
        except Exception:
            try:
                find[0].close()
            except Exception:
                pass
            
            if not handle_exception:
                raise
            
            print(error.html_render(context=1, headers=True))
            print("<br /><br />Found mode: {}<br />".format(common_f.get_val('mode', 'none')))
            print("Used mode: {}<br />".format(page_name))
            print("Page dict: {}<br />".format(str(page_dict[page_name])))
            print("Used path: {}<br />".format(path))
            
            exit()
    
    return the_page

start_time = time.time()

def main():
    # Need this so it uses the correct path
    try:
        for k, v in page_dict.items():
            v[1] = v[1].replace('gui/', '{}/gui/'.format(sys.path[0]))
    except Exception as e:
        print(error.html_render(context=1))
        raise
    
    import cgitb
    cgitb.enable(context=1)
    cgitb.html = error.html_render
    
    # Override the shell patterns to output HTML instead
    cli_f.shell_patterns = cli_f.html_patterns
    
    # Connect to DB
    cursor = database_f.get_cursor()
    
    # Default to listing players
    m = common_f.get_val('mode', pages.default_page)
    the_page = import_page(m)
    
    output = []
    
    try:
        page_results = the_page.main(cursor)
    except Exception as e:
        print("Content-type: text/html; charset=utf-8")
        print("")
        print("There was an error executing the main function of the_page: %s" % str(the_page).replace("<","&lt;").replace(">","&gt;"))
        print("<br /><br />")
        
        print(error.log_error(cursor, e, context=0))
        
        return
    
    # Is this an AJAX request?
    ajax = bool(common_f.get_val('ajax', False))
    
    # Redirect
    if page_results == "" and the_page.page_data.get("Redirect", "") != "":
        print("Location: {0}".format(the_page.page_data["Redirect"]))
        print("")
        return
    
    # Serving content
    print(the_page.page_data.get("Content-type", "Content-type: text/html; charset=utf-8"))
    print(html_f.cookies)
    print("")
    
    # Import the header/footer
    try:
        find = imp.find_module(the_page.page_data['Template'], ["templates"])
        the_template = imp.load_module("the_template", *find)
        find[0].close()
    except KeyError:
        print(error.html_render(context=1, headers=False))
        exit()
        
    except Exception:
        try:
            find[0].close()
        except Exception:
            pass
        
        print(error.html_render(context=1, headers=False))
        print("<br /><br />Found template: {}<br />".format(the_page.page_data['Template']))
        exit()
    
    # Headers
    if the_page.page_data.get("Headers", True) and page_results != "" and ajax != True:
        output.append(the_template.headers(cursor, the_page.page_data))
    
    # Core output
    output.append(page_results)
    
    the_page.page_data['time'] = time.time() - start_time
    
    # Footers
    if the_page.page_data.get("Headers", True) and page_results != "" and ajax != True:
        output.append(the_template.footers(cursor, the_page.page_data))
    
    output = de_unicode("".join([str(i) for i in output]))
    
    # We now want to print it out, sometimes there can be errors
    # related to unicode
    try:
        print(output)
    except UnicodeEncodeError as e:
        ignore_uni_errror = common_f.get_val("iue", 0)
        
        from profiteer import config
        try:
            f = open('%sutf8_out.html' % config.get('cache_path'), 'w', encoding='utf-8')
            f.write(output)
            f.close()
        except Exception:
            pass
        
        if ignore_uni_errror:
            _print_ignoring_error(output)
        
        o = output
        
        print("Unicode error at character %d, Ignore errors by adding '&iue=1', <a href='http://localhost/profiteer/utf8_out.html'>alternately view raw</a><br />" % e.start)
        print("%s<strong style='color:red;'>*</strong>%s" % (o[e.start-300:e.start].replace("<", "&lt;").replace(">", "&gt;"), o[e.start+1:e.start+20].replace("<", "&lt;").replace(">", "&gt;")))
        print("<br />")
        print(e.start, "<br />")
        print(dir(e))
        exit()
    except Exception as e:
        raise
