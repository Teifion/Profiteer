from profiteer import user, html_f
from profiteer.gui import login
import os

page_data = {
    "Template": "admin",
    "Title":    "Logout",
    "Padding":  10,
}

@user.require()
def main(cursor):
    user.logout(cursor)
    
    return "You are now logged out.<br /><br />{}".format(user.login_form("", ""))
