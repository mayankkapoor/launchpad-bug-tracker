#!/usr/bin/env python
'''
@Summary: Developer Script to search all Fix Committed and Fix Released bugs in Launchpad's Openstack projects (trunk merges only)

@Description: This script will generate an Excel report having the following:
1. Bug ID
2. Bug title
3. Date Created
4. Status
5. Importance
6. Fixed By
7. Fix Committed Date
8. Fix Released Date
9. Fixed-in Milestone
10. # of users affected
11. Users affected
12. Merge Revision Number
13. Has multiple branches?
14. Number of branches
15. Number of lines modified
16. Number of Files modified
17. Link to Diff text
18. List of Modified Files

@Pre-requisite:   Ensure xlwt python packages are installed.
@Status: version 1.0

@Email: rohit.karajgi@gmail.com
'''
from launchpadlib.launchpad import Launchpad
from datetime import datetime as dt
from optparse import OptionParser
import string
import time
import os
import sys
import xlwt

# Pass this in, from out
LP_LINK = 'https://bugs.launchpad.net/nova/+bug/'

class Bug:
    def __init__(self, bug, launchpad):
	self.launchpad = launchpad
	self.id = bug.bug.id
	self.title = bug.bug.title
	self.owner = bug.owner.name
	self.status = bug.status
	self.importance = bug.importance
	self.date_created = bug.date_created.strftime("%d-%m-%Y")
 	self.users_affected_count = bug.bug.users_affected_count
     	self.users_affected = self._get_users_affected(bug)
	self._set_variable_params(bug)

	self.merged_revno = 'N/A'
	self.num_lines_modified = ['N/A']
	self.num_files_modified = 'N/A'
	self.preview_diff_link = 'N/A'
	self.files_modified = ['N/A']
	self.lp_link = LP_LINK + str(self.id)
	self._set_merge_items(bug)

    def _get_branch_link(self,bug):
	self.has_multiple_branches = 'N'
	self.number_of_branches = len(bug.bug.linked_branches.entries)
	if self.number_of_branches == 0:
	    return None
	if self.number_of_branches > 1:
	    self.has_multiple_branches = 'Y'
        return bug.bug.linked_branches.entries[self.number_of_branches - 1]['branch_link']

    def _get_branch_m_p_link(self, branch):
        num = len(branch.landing_targets.entries)
	if num > 0:
            return self.launchpad.load(str(branch.landing_targets.entries[num - 1]['self_link']))
	return None

    def _get_users_affected(self,bug):
	users_collection = bug.bug.users_affected
 	users = ''
        for user in users_collection:
    	    name = self.launchpad.load(str(user))
    	    users = users + str(name.name) + ','
	return users.strip(',')

    def _set_variable_params(self,bug):
	if bug.date_fix_committed:
	    self.date_fix_committed = bug.date_fix_committed.strftime("%d-%m-%Y")
	else:
	    self.date_fix_committed = 'N/A'
	if bug.date_fix_released:
	    self.date_fix_released = bug.date_fix_released.strftime("%d-%m-%Y")
	else:
	    self.date_fix_released = 'N/A'
	if bug.milestone:
	    self.milestone = bug.milestone.title
	else:
	    self.milestone = 'none'
	if bug.assignee:
	    self.fixed_by = bug.assignee.name
	else:
	    self.fixed_by = 'Unassigned'

    def _get_lines_modified_per_file(self, preview):
	self.num_lines_modified = []
	for value in preview.diffstat.values():
	    self.num_lines_modified.append(value[0]+value[1])

    def _set_merge_items(self,bug):
        branch_link = self._get_branch_link(bug)
	if branch_link is not None:
            branch = self.launchpad.load(str(branch_link))
            branch_merge_proposal = self._get_branch_m_p_link(branch)
	    if branch_merge_proposal == None:
	        return
            preview = self.launchpad.load(str(branch_merge_proposal.preview_diff))
            self.merged_revno = branch_merge_proposal.merged_revno
            self.num_files_modified = len(preview.diffstat.keys())
	    if self.num_files_modified == 0 or self.num_files_modified == None:
		return
            self.files_modified = []
            for key in preview.diffstat.keys():
                file_name = str(key)
                self.files_modified.append(file_name)
	    self.preview_diff_link = string.replace(preview.self_link,"api.launchpad.net/1.0","code.launchpad.net")
            self.preview_diff_link +='/+files/preview.diff'
            self._get_lines_modified_per_file(preview)
	return

class Report:
    def __init__(self,bug_list):
	self.bug_list = bug_list
        self.workbook = xlwt.Workbook(encoding = 'ascii')
	self._set_styles()

    def _set_styles(self):
	heading_style = 'font: name Calibri, height 320, bold on, underline single; align: wrap on, horiz left, vert justified'
  	table_header_style = 'font: name Verdana, bold on ;align: wrap off, horiz center, vert center; borders: top medium, left medium, bottom medium, right medium'
	data_style = 'font: name Arial; align: wrap on, horiz center, vert justified; borders: top thin, left thin, bottom thin, right thin'
	bug_style = 'font: name Arial, color blue, underline single; align: wrap on, horiz center, vert justified; borders: top thin, left thin, bottom thin, right thin'
	self.heading_style = xlwt.easyxf(heading_style)
	self.table_header_style = xlwt.easyxf(table_header_style)
	self.table_data_style = xlwt.easyxf(data_style)
	self.bug_cell_style = xlwt.easyxf(bug_style)

    def create_spreadsheet(self, file_name, sheet_name, bug_count, statuses):
	if len(statuses) == 0:
	    statuses = 'ALL'
	heading = "Bug Report for Project: '%s'" % (sheet_name.upper())
	heading_line2 = "Status: %s     Count: %s" % (statuses,bug_count)
	as_of_date = 'Date: ' + dt.now().strftime("%d-%m-%Y")
	worksheet = self.workbook.add_sheet(sheet_name, cell_overwrite_ok = True)
	worksheet.write_merge(0,0,0,6,heading, self.heading_style)
	worksheet.write_merge(0,0,7,9,as_of_date, self.heading_style)
	worksheet.write_merge(1,1,0,7,heading_line2, self.heading_style)
        worksheet.set_panes_frozen(True) # frozen headings instead of split pane
        worksheet.set_horz_split_pos(3) # in general, freeze after last heading row

	header_map = {0:'S.No', 1:'Bug ID', 2:'Title', 3:'Owner', 4:'Date Created', 5:'Status', 6:'Importance', 7:'Fixed By', 8:'Fix Committed Date', 9:'Fix Released Date', 10:'Fixed-in Milestone', 11:'# of users affected', 12:'Users Affected', 13:'Merged Rev. #', 14: 'Has Multiple Branches?', 15:'# of Branches', 16:'# of Files modified', 17:'List of Files Modified', 18:'# of Lines Modified per file', 19:'Link to Diff text'}

	worksheet.col(2).width = len(header_map[2])*9*256
	worksheet.col(3).width = len(header_map[3])*3*256
	for i in range(4,20):
	    worksheet.col(i).width = (len(header_map[i])+4)*256

	for key in header_map.keys():
   	    worksheet.write(2,key,header_map[key], self.table_header_style)
	row = 3
	count = 0
	for bug_obj in self.bug_list:
	    count = count + 1
	    files_list_length = len(bug_obj.files_modified)
	    worksheet.write(row,0, count,self.table_data_style)
	    worksheet.write(row,1, xlwt.Formula('HYPERLINK("%s";"%s")' % (bug_obj.lp_link,bug_obj.id)), self.bug_cell_style)
	    worksheet.write(row,2, bug_obj.title, self.table_data_style)
	    worksheet.write(row,3, bug_obj.owner, self.table_data_style)
	    worksheet.write(row,4, bug_obj.date_created, self.table_data_style)
	    worksheet.write(row,5, bug_obj.status, self.table_data_style)
	    worksheet.write(row,6, bug_obj.importance, self.table_data_style)
	    worksheet.write(row,7, bug_obj.fixed_by, self.table_data_style)
	    worksheet.write(row,8, bug_obj.date_fix_committed, self.table_data_style)
	    worksheet.write(row,9, bug_obj.date_fix_released, self.table_data_style)
	    worksheet.write(row,10, bug_obj.milestone.replace('OpenStack ',''), self.table_data_style)
	    worksheet.write(row,11, bug_obj.users_affected_count, self.table_data_style)
	    worksheet.write(row,12, bug_obj.users_affected, self.table_data_style)
	    worksheet.write(row,13, bug_obj.merged_revno, self.table_data_style)
	    worksheet.write(row,14, bug_obj.has_multiple_branches, self.table_data_style)
	    worksheet.write(row,15, bug_obj.number_of_branches, self.table_data_style)
	    worksheet.write(row,16, bug_obj.num_files_modified, self.table_data_style)
	    if files_list_length <= 1:
	        worksheet.write(row,17, bug_obj.files_modified[0], self.table_data_style)
	        worksheet.write(row,18, bug_obj.num_lines_modified[0], self.table_data_style)
	    worksheet.write(row,19, xlwt.Formula('HYPERLINK("%s";"Diff")' % (bug_obj.preview_diff_link)), self.bug_cell_style)
	    if files_list_length > 1:
		worksheet.write(row,17, '', self.table_data_style)
		worksheet.write(row,18, '', self.table_data_style)
		for i in range(0,files_list_length):
	            row = row + 1
		    for j in range(0,17):
                       worksheet.write(row,j, '', self.table_data_style)
		    worksheet.write(row,17, bug_obj.files_modified[i], self.table_data_style)
		    worksheet.write(row,18, bug_obj.num_lines_modified[i], self.table_data_style)
		    worksheet.write(row,19, '', self.table_data_style)
	    row = row + 1

	self.workbook.save(file_name)

def check_cachedir():
    cachedir = os.path.join(os.getcwd(),'.launchpadlib/cache/')
    try:
        if not os.path.isdir(cachedir):
	    print "Creating launchpadlib cache directory at %s" % cachedir
            os.mkdir(cachedir)
	    return cachedir
    except:
	raise

def get_kv(myhash):
    arr = ''
    for k,v in myhash.iteritems():
        arr = arr+k+'='+v+', '
    return arr.rstrip(', ')

def main():
    argv = sys.argv
    arglen = len(argv)

    usage = "usage: %prog project [options]\nproject should be either 'nova' or 'swift' or 'glance'\nSee -h or --help for detailed usage."
    status_map = {'c':'Confirmed', 'fc':'Fix Committed', 'fr':'Fix Released', 'ip':'In Progress', 'ic':'Incomplete', 'i':'Invalid', 'n':'New', 'o':'Opinion', 't':'Triaged', 'w':'Won\'t Fix'}
    imp_map = {'c':'Critical', 'h':'High', 'm':'Medium', 'l': 'Low', 'u':'Unknown', 'w':'Wishlist', 'ud':'Undecided'}

    parser = OptionParser(usage=usage, version="%prog 1.0")
    parser.add_option("-s", "--status", help="Bug status or list of comma separated values. Default: fc,fr \n[Values: %s]"%get_kv(status_map), dest="status", default="fc,fr")
    parser.add_option("-i", "--imp", help="Bug Importance or list of comma separated values. Default: all \n[Values: %s]"%get_kv(imp_map), dest="imp", default=[])
    (options, args) = parser.parse_args(args=None, values=None)

    if arglen == 1:
        sys.exit(parser.print_usage())

    lb = 'Show only Bugs with linked Branches'
    project = argv[1]
    statuses = options.status.split(',')
    if statuses[0] == 'all':
	statuses = []
	lb = 'Show all bugs'
    else:
        statuses = [status_map[status] for status in statuses]
    if len(options.imp) != 0:
        imps  = options.imp.split(',')
	imps = [imp_map[imp] for imp in imps]
    else:
	imps = []

    cachedir = check_cachedir()
    launchpad = Launchpad.login_anonymously('scour bugs','production', cachedir)

    lp_project = launchpad.projects[project]
    bugs = lp_project.searchTasks(status=statuses, importance=imps, linked_branches=lb)
    bug_count = 0
    print "Querying Launchpad for bugs and tracking the time taken. This may take many minutes depending on the number of bugs"
    bug_obj_list = []
    start = time.time()
    for bug in bugs:
        bug_obj = Bug(bug, launchpad)
        bug_obj_list.append(bug_obj)
        bug_count = bug_count + 1
        print "Bugs Processed: %s, Id: #%s" % (bug_count,str(bug_obj.id))
    date_stamp = dt.now().strftime("%d%m%Y_%H%M%S")
    filename = 'BugReport_'+project+'_'+date_stamp+'.xls'
    report = Report(bug_obj_list)
    report.create_spreadsheet(filename, project, bug_count, statuses)
    print "Report generated.\nFilename: '%s' in current working directory." % filename
    end = time.time()
    elapsed = end - start
    min = elapsed/60
    print "Time taken = ", round(min,2), " minutes (or ", round(elapsed,2), " seconds)"

if __name__ == '__main__':
    main()
