Admin GUI pages (such as list_players) are designed to provide a graphical
interface to the underlying tools and data of the program.

page_data
=========
Each page has a dictionary defined in it with several possible keys.

General
-------
 * Title: The HTML title used for the page
 * Admin: If set to True then it will use Admin headers and menus on the page
 * Redirect: If set to a non-empty string this page will HTTP redirect
 * Content-type: You can override the default content type (such as for images)

Layout
------
 * Headers: If set to False then no headers will be printed
 * css: If set to a string then custom CSS will be placed on the page
 * js: If set to a string then custom JS will be placed on the page
 * js_libs: A list of JS libraries to include in addition to jquery
 * Padding: The amount of padding in the content div

Dynamic
-------
 * Filters: A list of lists/tuples, each first item is a link and the second the text
    and the third if it's selected, filters appear at the top of the content
    block. If the item is a string rather than a list then it's taken as raw
    html and simply inserted.
 * Filter_html: Raw HTML inserted into the filter bar, if Filters is non-empty it will insert
    this HTML after the list
 * Rows: The number of rows returned by the query, the number will appear in the top
    right corner of the content block or if it's there, the filter block


