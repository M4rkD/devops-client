from azure.devops.connection import Connection
from azure.devops.v6_0.work_item_tracking import Wiql
from msrest.authentication import BasicAuthentication

# Fill in with your personal access token and org URL
personal_access_token = 'iywk3uook2xwvsmjhoztcb7qvka4qrpjvdtjicgaif3ofy5x4gbq'
organization_url = 'https://dev.azure.com/swansea-university'
project_name = 'Swansea Academy of Advanced Computing'

# Create a connection to the org
credentials = BasicAuthentication('', personal_access_token)
connection = Connection(base_url=organization_url, creds=credentials)

# connection.get_client('azure.devops.released.core.core_client.CoreClient')

# Get clients
# the "core" client provides access to projects, teams, etc
client = connection.clients.get_core_client()
# the "work item track" client provides access to work items
wit_client = connection.get_client('azure.devops.v6_0.work_item_tracking.work_item_tracking_client.WorkItemTrackingClient')

def all_teams():
    return client.get_teams(project_id=project_name)

def query_work_items(q):
    work_item_references = wit_client.query_by_wiql(Wiql(q)).work_items

    work_item_ids = [item.id for item in work_item_references]

    return work_items_by_id(work_item_ids)


def work_items_by_id(work_item_ids):
    work_items = wit_client.get_work_items(ids=work_item_ids)

    work_item_data = { wi.id : wi.as_dict() for wi in work_items }

    return work_item_data

def project_workitems(team_name):

    q = f"SELECT * FROM workitems WHERE [System.AreaPath] = 'Swansea Academy of Advanced Computing\{team_name}'"

    return query_work_items(q)

# project = get_first_project(client)
# wit_client = get_work_item_client(client)


# some samples here
# https://github.com/microsoft/azure-devops-python-samples/blob/master/src/samples/work_item_tracking.py

team = all_teams()[0]

team_name = 'AerOpt'
work_items = project_workitems(team_name)


# classified_work_items = { wi.fields['System.WorkItemType'] : [] for wi in wis }
# 
# for wi in wis:
#     classified_work_items[wi.fields['System.WorkItemType']].append(wi.fields)
# 
# epics = [ wi.fields for wi in wis if wi.fields['System.WorkItemType'] == 'Epic' ]


print('hi')
#

ex = 46108

work_item = wit_client.get_work_items(ids=[ex], expand='All')[0] # get all
work_item.relations # get list of relations

def id_from_url(url):
    return int(url.split('/')[-1])

def related_work_items(work_item):
    ids = [
        id_from_url(rel.url)
        for rel in work_item.relations
    ]

    return wit_client.get_work_items(ids=ids)


#a = wit_client.get_reporting_links_by_link_type(project=project_name)

k = related_work_items(work_item)


children = [j['fields']['System.Title'] for j in k.values()]
