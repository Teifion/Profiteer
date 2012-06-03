from profiteer import common_f, html_f, config, user

page_data = {
    "Template":             "admin",
    "Title":                "Login",
    "password_incorrect":   False
}

@user.require()
def main(cursor, message=""):
    username = common_f.get_val('username', '')
    password = common_f.get_val('password', '')
    
    # No details, show the login default page
    if username == "" or password == "":
        return """<script type="text/javascript" charset="utf-8">
            setTimeout("document.location='web.py';");
        </script>"""
    
    response = user.attempt_login(cursor)
    
    if type(response) != str and response != None:
        return """<script type="text/javascript" charset="utf-8">
            setTimeout("document.location='web.py';");
        </script>"""
    
    return user.login_form(response, username=username)


