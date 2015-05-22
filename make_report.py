"""This script generates statistical charts from Launchpad Bug report .xls sheet created by bugseeker.py

Following charts are generated:
    1. Distribution By Status
    2. Distribution By Owner
    3. Distribution By Importance
    4. Distribution By Milestone
    5. Distribution by Fixed-by
    6. # of times a file was modified
    7. # of lines modified per file

Pre-requisites: bugseeker.py has been run and Bug Report(.xls) spreadsheet is generated
Dependent Packages: xlrd (pip install), cairoplot (bzr branch lp:cairoplot)
"""

__author__ = "Rohit Karajgi"
__version__ = "1.0.1"
__maintainer__ = "Rohit Karajgi"
__email__ = "rohit.karajgi@gmail.com"
__status__ = "Development"
__date__ = "June 6, 2011"

from collections import defaultdict
from datetime import datetime as dt
import subprocess
import shutil
import os
import re
import xlrd
import cairoplot
import markup

REPORTS_ROOT='/var/lib/jenkins/LPReports/'

def get_latest_reports_dir():
    """Search the Reports folder for the latest .xls report and return the latest folder and filepath"""
    pipe = subprocess.Popen(["/bin/ls", "-t", REPORTS_ROOT], stdout=subprocess.PIPE)
    output,err = pipe.communicate()
    folder = output.split()[0]
    latest_dir = os.path.join(REPORTS_ROOT,folder)
    pipe2 = subprocess.Popen(["/bin/ls", "-t", latest_dir], stdout=subprocess.PIPE)
    filepath,err = pipe2.communicate()
    return folder, filepath.split()[0].strip()

folder, filename = get_latest_reports_dir()
absolute_file_path = os.path.join(REPORTS_ROOT,folder,filename)

"""Create charts directory and declare chart file paths"""
reports_dir = os.path.join(REPORTS_ROOT,folder)
charts_dir = os.path.join(reports_dir,"charts")
os.mkdir(charts_dir)
os.mkdir(reports_dir+"/images")
shutil.copy2('/var/lib/jenkins/images/vertex_ntt.png',reports_dir+'/images/')
owners_chart = os.path.join(charts_dir,'owners.png')
status_chart = os.path.join(charts_dir,'status.png')
imps_chart = os.path.join(charts_dir,'imps.png')
fixers_chart = os.path.join(charts_dir,'fixers.png')
miles_chart = os.path.join(charts_dir,'miles.png')

wb = xlrd.open_workbook(absolute_file_path)
sh = wb.sheet_by_index(0)

"""Get required columns from .xls as lists"""
total_bugs = sh.col_values(0)
owners = sh.col_values(3)
statuses = sh.col_values(5)
imps = sh.col_values(6)
fixers = sh.col_values(7)
miles = sh.col_values(10)
files_mod = sh.col_values(17)
lines_list = sh.col_values(18)
miles = [val.replace('Compute ','') for val in miles]

def pop3(column):
    """Pop out the first 3 rows from the column"""
    for i in range(3):
	column.pop(0)

for each_column in (owners, statuses, imps, fixers, miles, files_mod, lines_list):
    pop3(each_column)

# Create a copy of files_mod to be used later
files_list = files_mod

# Create a regex object for .py files
pattern = '.*.py$'
regx = re.compile(pattern)

"""filter out all the blanks in the columns"""
owners = filter(lambda item: len(item)>0,owners)
statuses = filter(lambda item: len(item)>0,statuses)
imps = filter(lambda item: len(item)>0,imps)
fixers = filter(lambda item: len(item)>0,fixers)
miles = filter(lambda item: len(item)>0,miles)
files_mod = filter(lambda item: re.search(regx,item), files_mod)         # Filter only .py files
total_bugs = len(owners)

def count_dups(col_list):
    """Count occurrences of each item in the column and return a list of tuples having item and number of occurrences of the item"""
    uniqueSet = set(item for item in col_list)
    return [(item, col_list.count(item)) for item in uniqueSet]

"""Get count of bugs by Owner, Status, Importance, Fixed-by, Milestone, and number of bugs in which a file was modified (Covers 6 graphs)"""
owners_count = count_dups(owners)
statuses_count = count_dups(statuses)
imps_count = count_dups(imps)
fixers_count = count_dups(fixers)
miles_count = count_dups(miles)
files_mod_count = count_dups(files_mod)
sorted_owners_count = sorted(owners_count, key=lambda x: x[1], reverse=True)
sorted_imps_count = sorted(imps_count, key=lambda x: x[1])
sorted_fixers_count = sorted(fixers_count, key=lambda x: x[1], reverse=True)
sorted_miles_count = sorted(miles_count, key=lambda x: x[1])
sorted_files_mod_count = sorted(files_mod_count, key=lambda x: x[1], reverse=True)


def get_file_indices(seq):
    """Get the row indices of each occurance of a file in the files column and return tuple containing filename and list of indices"""
    tally = defaultdict(list)
    for i,item in enumerate(seq):
        tally[item].append(i)
    return ((key,locs) for key,locs in tally.items()
                            if len(locs)>=1)

files_map = []
for item in (get_file_indices(files_list)):
    files_map.append(item)

only_py_files_map = filter(lambda item: re.search(regx,item[0]), files_map)

"""Get list files and number of lines modified for each file (Graph 7) and create a list of tuples"""
files_to_lines = []
for file_item in only_py_files_map:
    line_sum = 0
    for row_num in file_item[1]:
	line_sum = line_sum + lines_list[row_num]
    files_to_lines.append((file_item[0],int(line_sum)))

sorted_files_to_lines = sorted(files_to_lines, key=lambda x: x[1], reverse=True)

def plot_chart(param, img_file, width=1040, height=480):
    """Get the parameter list and plot Vertical bar chart"""
    data = [[val[1]] for val in param]
    chart = cairoplot.VerticalBarPlot(img_file, data, width, height, background=None, border=20, grid=True, x_labels=[val[0] for val in param],three_dimension=False, display_values=True, series_colors="custom")
    chart.render()
    chart.commit()

plot_chart(sorted_owners_count[:15], owners_chart, width=1200)
plot_chart(statuses_count, status_chart)
plot_chart(sorted_imps_count, imps_chart, width=750)
plot_chart(sorted_fixers_count[:15], fixers_chart, width=1280)
plot_chart(sorted_miles_count, miles_chart, width=1200)

def make_files_mod_table(reports_dir, sorted_files_mod_count):
    """Using the sorted list of files modified, create the HTML table"""
    page = markup.page()
    count = 1
    page.init(title="Launchpad Bug report")
    page.table(border="2", cellspacing="0", cellpadding="4", width="50%", style="font-family:Verdana, sans-serif; text-align:left")
    page.th("S/N")
    page.th("Modified File")
    page.th("# of times modified")
    for item in sorted_files_mod_count:
        page.tr()
        page.td(count)
        page.td(str(item[0]))
        page.td(str(item[1]))
	page.tr.close()
        count = count + 1
    page.table.close()
    html = open(reports_dir+'/files_count.html', 'w')
    html.write(str(page))
    html.close()

def make_lines_mod_table(reports_dir, sorted_files_to_lines):
    """Using the sorted list of lines modified per file, create the HTML table"""
    page = markup.page()
    count = 1
    page.init(title="Launchpad Bug report")
    page.table(border="2", cellspacing="0", cellpadding="4", width="50%", style="font-family:Verdana, sans-serif; text-align:left")
    page.th("S/N")
    page.th("File Path")
    page.th("# of lines modified till date")
    for item in sorted_files_to_lines:
        page.tr()
        page.td(count)
        page.td(str(item[0]))
        page.td(str(item[1]))
	page.tr.close()
        count = count + 1
    page.table.close()
    html = open(reports_dir+'/lines_count.html', 'w')
    html.write(str(page))
    html.close()

def make_owners_count_table(reports_dir, sorted_owners_count):
    """Using the sorted list of owners, create the HTML table"""
    page = markup.page()
    count = 1
    page.init(title="Launchpad Bug report")
    page.table(border="2", cellspacing="0", cellpadding="4", width="50%", style="font-family:Verdana, sans-serif; text-align:left")
    page.th("S/N")
    page.th("Bug Owner")
    page.th("# of Bugs filed")
    for item in sorted_owners_count:
        page.tr()
        page.td(count)
        page.td(str(item[0]))
        page.td(str(item[1]))
	page.tr.close()
        count = count + 1
    page.table.close()
    html = open(reports_dir+'/owners.html', 'w')
    html.write(str(page))
    html.close()

def make_fixers_count_table(reports_dir, sorted_fixers_count):
    """Using the sorted list of Fixed-by names, create the HTML table"""
    page = markup.page()
    count = 1
    page.init(title="Launchpad Bug report")
    page.table(border="2", cellspacing="0", cellpadding="4", width="50%", style="font-family:Verdana, sans-serif; text-align:left")
    page.th("S/N")
    page.th("Bug Fixer/Assignee")
    page.th("# of Bugs fixed")
    for item in sorted_fixers_count:
        page.tr()
        page.td(count)
        page.td(str(item[0]))
        page.td(str(item[1]))
	page.tr.close()
        count = count + 1
    page.table.close()
    html = open(reports_dir+'/fixers.html', 'w')
    html.write(str(page))
    html.close()

def make_html(reports_dir, filename, total_bugs):
    """Function to create the HTML chart from Launchpad Bug report xls"""
    page = markup.page()
    page.init(title="Launchpad Bug report")
    page.a(name="top")
    page.img(src="images/logo.png", alt="Company_Logo", align="right")
    page.h1("LAUNCHPAD BUG REPORT - OpenStack NOVA     (%s)"%dt.now().strftime("%d-%m-%Y"), style="font-family:Verdana,sans-serif; font-size:18pt; color:rgb(96,0,0)")
    page.hr()
    page.h1("Total Bug Count: %s"%total_bugs, style="font-family:Verdana,sans-serif; font-size:16pt; color:006699")
    page.a("Download .xls Report", href="./"+filename)
    page.br()
    page.br()
    page.a("1. Bug Distribution - By Status", href="#c1", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")
    page.br()
    page.a("2. Bug Distribution - By Importance", href="#c2", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")
    page.br()
    page.a("3. Bug Distribution - By Milestone", href="#c3", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")
    page.br()
    page.a("4. Bug Distribution - By Bug owners", href="#c4", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")
    page.br()
    page.a("5. Bug Distribution - By Fixed-by", href="#c5", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")
    page.br()
    page.a("6. # of times a file was modified", href="files_count.html", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")
    page.br()
    page.a("7. # of lines modified per file", href="lines_count.html", style="text-decoration:none; font-family:Verdana,sans-serif; font-size:12")

    for i in range(2):
        page.br()
    page.a(name="c1")
    page.h1("1.  Bug Distribution - By Status",  style="font-family:Verdana,sans-serif; font-size:14pt; color:rgb(136,0,0)")
    page.img(src="charts/status.png", alt="Statuses Chart")
    page.a("Top", href="#top", style="align:right")
    page.br()
    page.a(name="c2")
    page.h1("2. Bug Distribution - By Importance", style="font-family:Verdana,sans-serif; font-size:14pt; color:rgb(136,0,0)")
    page.img(src="charts/imps.png", alt="Importance Chart")
    page.a("Top", href="#top", style="align:right")
    page.br()
    page.a(name="c3")
    page.h1("3. Bug Distribution - By Milestone", style="font-family:Verdana,sans-serif; font-size:14pt; color:rgb(136,0,0)")
    page.img(src="charts/miles.png", alt="Milestone Chart")
    page.a("Top", href="#top", style="align:right")
    page.br()
    page.a(name="c4")
    page.h1("4. Bug Distribution - By Bug owners (Top 15)", style="font-family:Verdana,sans-serif; font-size:14pt; color:rgb(136,0,0)")
    page.a("Click here for complete table", href="owners.html")
    page.img(src="charts/owners.png", alt="Owners Chart")
    page.a("Top", href="#top", style="align:right")
    page.br()
    page.a(name="c5")
    page.h1("5. Bug Distribution - By Fixed-by (Top 15)", style="font-family:Verdana,sans-serif; font-size:14pt; color:rgb(136,0,0)")
    page.a("Click here for complete table", href="fixers.html")
    page.img(src="charts/fixers.png", alt="Fixers Chart")
    page.a("Top", href="#top", style="align:right")
    html = open(reports_dir+'/index.html', 'w')
    html.write(str(page))
    html.close()

"""Make all the HTML files"""
make_files_mod_table(reports_dir, sorted_files_mod_count)
make_lines_mod_table(reports_dir, sorted_files_to_lines)
make_owners_count_table(reports_dir, sorted_owners_count)
make_fixers_count_table(reports_dir, sorted_fixers_count)
print "Creating HTML reports..."
make_html(reports_dir, filename, total_bugs)
