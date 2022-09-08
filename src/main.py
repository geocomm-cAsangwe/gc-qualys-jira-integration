from http import cookies
from requests.auth import HTTPBasicAuth
from wsgiref import headers
import csv
import json
import requests
import os

# This is a python script that automates the process of retrieving vulnerability
# information from Qualys scans and creating Jira tickets based on the details of a scans.

# Files
scanresults = "scanresults.csv"  # scan results

# API endpoints
session = "https://qualysapi.qg4.apps.qualys.com/api/2.0/fo/session/"
asset = "https://qualysapi.qg4.apps.qualys.com/api/2.0/fo/asset/group/"
scan = "https://qualysapi.qg4.apps.qualys.com/api/2.0/fo/scan/"


headers = {
    "X-Requested-With": "Qualys-Session",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Functions

######################################################################
#-------------------------- JIRA API --------------------------------#
######################################################################

# Jira function to create tickets


def createJiraTicket():
    auth = HTTPBasicAuth(user, jtoken)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "update": {},
        "fields": {
            "project":
            {
                "key": jkey
            },
            "summary": "Qualys_VMDR_" + qtitle,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Threat: " + threat + "\n" "\n" + "Impact: " + impact + "\n" "\n" + "Solution: " + solution
                            }
                        ]
                    }
                ]
            },
            "priority": {
                "id": priority
            },
            "issuetype": {
                "name": "Defect"
            },
        }
    })

    response = requests.request(
        "POST", url, data=payload, headers=headers, auth=auth)

    jsonResults = (json.dumps(json.loads(response.text),
                              sort_keys=True, indent=4, separators=(",", ": ")))
    # print(jsonResults)

#--------------------------------------------------------------------#

######################################################################
#------------------------- QUALYS API -------------------------------#
######################################################################

# Login and retrieve session id.

# Login function


def login():
    # replace with user preference.
    data = "action=login&username=gecmm6ca&password=5R55lL77F2!"
    res = requests.post(session, headers=headers, data=data)
    if res.status_code == 200:
        print('Logged in')
    else:
        print(res.status_code)
    cookies = (res.cookies)
    return cookies

#--------------------------------------------------------------------#

# Logout Function


def logout():
    data = "action=logout"
    res = requests.post(session, headers=headers,
                        data=data, cookies=cookies)
    if res.status_code == 200:
        print('Logged out')
    else:
        print(res.status_code)

######################################################################
#------------------------ Add Information ---------------------------#
######################################################################

# function to add asset group
# **Only run this function when needing to add a new Asset Group**


def newAG():
    print('Creating new asset group based on details provided.')
    data = {
        'action': 'add',
        'echo_request': '1',
        'ips': ips,
        'title': agtitle
    }
    res = requests.request('POST', asset, cookies=cookies,
                           headers=headers, data=data)
    if res.status_code == 200:
        print('Asset group created')
    else:
        print(res.status_code)
#--------------------------------------------------------------------#
# function to launch a new scan

# **Only run this function when needing to launch new scans**
# **Use Asset group details from Qualys UI or use recently added Asset Group**


def launchScan():
    print('Launching a scan')
    data = {
        'action': 'launch',
        'echo_request': '1',
        'scan_title': agtitle + ' VMDR Scan',
        'target_from': 'assets',
        'asset_groups': agtitle,
        'option_title': optiontitle
    }
    res = requests.request('POST', scan, headers=headers,
                           cookies=cookies, data=data)
    if res.status_code == 200:
        print('Scan Launched!')
    else:
        print(res.status_code)


######################################################################
#---------------------Information Provided---------------------------#
######################################################################

# Function to download scan results

def scanResults():
    print("Downloading scan results...")
    data = {
        'action': 'fetch',
        'scan_ref': scanid,
        'mode': 'extended',
        'output_format': 'csv_extended'
    }
    res = requests.request("POST", scan, cookies=cookies,
                           headers=headers, data=data)
    if res.status_code == 200:
        print('Scan results downloaded')
        # save results to a csv file.
        with open(scanresults, "wb") as f:
            f.write(res.content)

    else:
        print(res.status_code)

######################################################################
#------------------------- User Operation ---------------------------#
######################################################################
# **Simply comment out task (functions) user does not need to run**


# Jira Variables - Replace with user preference
user = os.environ.get('jira_user')
jtoken = os.environ.get('jira_token')
jkey = os.environ.get('jira_key')
url = os.environ.get('jira_url')

# Qualys Variables - Replace with user preference
agtitle = os.environ.get('qualys_assetgroup')
ips = os.environ.get('qualys_ips')
optiontitle = os.environ.get('qualys_optiontitle')
scanid = os.environ.get('qualys_scanid)

# Log into Qualys API and store session ID
cookies = login()

# add asset groups (**If needed**)
# newAG()  # call function.

# Log out when completed.
# logout()  # call function.

# Launch a scan (**If needed**)
# launchScan()  # call function.

# Log out when completed.
# logout()  # call function.

# Download the scan results.
scanResults()  # call function.

# Log out when completed.
logout()  # call function.

######################################################################
#--------------------- Retrieve Scan Details ------------------------#
######################################################################
print('Creating Jira Tickets...')

with open(scanresults) as f:
    # **Skip lines 1-7 in the csv file.**
    for i in range(7):
        next(f)
    reader = csv.DictReader(f)
    for row in reader:
        if (row['QID']) != None:
            qid = (row['QID'])
        if (row['Title']) != None:
            qtitle = (row['Title'])
        if (row['Severity']) != None:
            severity = (row['Severity'])
        if (row['Threat']) != None:
            threat = (row['Threat'])
        if (row['Impact']) != None:
            impact = (row['Impact'])
        if (row['Solution']) != None:
            solution = (row['Solution'])
        if severity == '5':
            priority = '1'
            createJiraTicket()
        elif severity == '4':
            priority = '2'
            createJiraTicket()
        elif severity == '3':
            priority = '3'
            createJiraTicket()
        elif severity == '2':
            priority = '4'
            createJiraTicket()
        elif severity == '1':
            priority = '5'

        # Create Jira Tickets, [row by row]
        # if qtitle != None:
        #     createJiraTicket()

print('Process Complete. View appropriate interface for confirmation.')
