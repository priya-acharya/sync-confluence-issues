import base64
import os
import pyconfluence
import gspread
from jira import JIRA
from pyconfluence.actions import edit_page,get_page_content,convert_storage_to_view
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from constants import allowed_team_members

def googlesheet_authenticate():
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('src\google_token.json',scope)
    gclient = gspread.authorize(credentials)
    return gclient

def set_confluence_environment():
    #os.environ['AUTH'] = bytes('MTAyMTQyMjokVFBOYTIwMTc=')
    os.environ['PYCONFLUENCE_TOKEN'] = base64.b64decode( os.environ['AUTH'].encode( 'utf-8' ) ).decode( 'utf-8' ).split(':')[1].strip()
    os.environ['PYCONFLUENCE_USER'] = '1021422'
    os.environ['PYCONFLUENCE_URL'] = 'https://confluence.jda.com'

def get_fields_JIRA(jira_list): 
    jira_result = {}

    username = base64.b64decode( os.environ['AUTH'].encode( 'utf-8' ) ).decode( 'utf-8' ).split(':')[0].strip() 
    password = base64.b64decode( os.environ['AUTH'].encode( 'utf-8' ) ).decode( 'utf-8' ).split(':')[1].strip()
    
    jira = JIRA(basic_auth=(username,password),options = {
    'server' : 'https://jira.jda.com',
    'verify' : False,
    })

    for jira_id in jira_list:
        issue = jira.issue(jira_id)

        count = 0
        qa_jiraId = ""
        qa_status = ""
        qa_assignee = ""

        dev_assignee = issue.fields.assignee.displayName
        dev_status = issue.fields.status.name
        salesforce = "Internal" if issue.fields.customfield_14202 != None and issue.fields.customfield_14202[0] == "0017000000Ll0lFAAR" else "Customer"
        subtasks_list = issue.fields.subtasks
        for task in subtasks_list:
            qa_issue = jira.issue(task.key)
            if qa_issue.fields.issuetype.name == "Testing task":
                qa_status = qa_issue.fields.status.name
                qa_jiraId = task.key
                qa_assignee = qa_issue.fields.assignee.displayName
                count +=1
        if count == 0:
            qa_status = "NA" if dev_status == "Closed" else "To Be Created"
            qa_jiraId = "NA"
            qa_assignee = "Unassigned" if qa_status == "To Be Created" else "NA"

        jira_result[jira_id] = [qa_jiraId,dev_assignee,qa_assignee,dev_status,qa_status,salesforce]
        
    return jira_result

def get_defects_confluence():

    confluence_map = {}
    set_confluence_environment()

    xhtml = get_page_content('170131867') 
    data = convert_storage_to_view(xhtml)

    # Read the html code 
    soup = BeautifulSoup(data,"html.parser")

    defects_table = soup.find(id="Defects").findNext('table')
    defects_rows = defects_table.find_all('tr')
 
    for tr in defects_rows:
        row_data = tr.find_all('td')

        if( len(row_data) == 0 or row_data[4].text.strip() == ""):
            continue
        
        #Take values only when Assigned is not empty         
        values =  [row_data[0].text.strip(),'',row_data[8].text.strip(),row_data[2].text.strip(),row_data[3].text.strip(),row_data[13].text.strip(),row_data[4].text.strip(),'',row_data[5].text.strip(),'','',row_data[7].text.strip().split(' ')[0]] if row_data[4].text.strip() != "" else None

        if(values is not None and values[6] in allowed_team_members):
            confluence_map[values[0]] = values
    return confluence_map
    
def get_defects_googlesheet():
    
    googlesheet_map = {}
    
    gc = googlesheet_authenticate()
    googledefects_workbook = gc.open('Automation addition progress sheet')
    
    google_defects_worksheet = googledefects_workbook.worksheet('Qa Work Progress')  
    googlesheet_list = google_defects_worksheet.get_all_values()
    iterable_list = googlesheet_list[1:]

    for row in iterable_list:
        jira_id = row[0]
        googlesheet_map[jira_id] = row

    return google_defects_worksheet,googlesheet_map

def union_keys(some_dict, another_dict):
    temp_dict = some_dict.copy( )
    temp_dict.update(another_dict)
    return temp_dict.keys()

def update_defects_googlesheet():    
    confluence_map = get_defects_confluence()
    google_defects_worksheet , googlesheet_map = get_defects_googlesheet()
    jira_set = union_keys(confluence_map,googlesheet_map)
    row_count = len(googlesheet_map)

    for jira_id in jira_set:

        if jira_id in googlesheet_map and jira_id in confluence_map:
            # update in google sheet 
            cell = google_defects_worksheet.find(jira_id)
            cell_range = google_defects_worksheet.range('A'+str(cell.row)+':L'+str(cell.row))
            i = 0
            for cell in cell_range:
                cell.value = confluence_map[jira_id][i]
                i +=1
            google_defects_worksheet.update_cells(cell_range) 
        
        elif jira_id not in googlesheet_map and jira_id in confluence_map:
            # insert row into google sheet 
            cell_range = google_defects_worksheet.range('A'+str(row_count+2)+':L'+str(row_count+2))
            i = 0
            for cell in cell_range:
                cell.value = confluence_map[jira_id][i]
                i +=1
            google_defects_worksheet.update_cells(cell_range)

            #Increment as a new row has been inserted            
            row_count +=1
    
    #Once all rows have been modified/inserted, update the JIRA fields in these rows
    jira_fields = get_fields_JIRA(jira_set)
    
    # Update the rest of the fields from JIRA 
    for key in jira_fields:
        cell_to_update = google_defects_worksheet.find(key)
        google_defects_worksheet.update_acell("B"+str(cell_to_update.row),jira_fields[key][0])
        google_defects_worksheet.update_acell("G"+str(cell_to_update.row),jira_fields[key][1])
        google_defects_worksheet.update_acell("H"+str(cell_to_update.row),jira_fields[key][2])
        google_defects_worksheet.update_acell("I"+str(cell_to_update.row),jira_fields[key][3])
        google_defects_worksheet.update_acell("J"+str(cell_to_update.row),jira_fields[key][4])
        google_defects_worksheet.update_acell("K"+str(cell_to_update.row),jira_fields[key][5])


if __name__ == '__main__':
    update_defects_googlesheet()


