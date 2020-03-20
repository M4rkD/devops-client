import json

from msrest import Configuration
from msrest.authentication import BasicAuthentication
from msrest.service_client import ServiceClient
from msrest.universal_http import ClientRequest

fields = [
 'System.Id'
 'System.AreaId'
 'System.AreaPath'
 'System.TeamProject'
 'System.NodeName'
 'System.AreaLevel1'
 'System.AreaLevel2'
 'System.Rev'
 'System.AuthorizedDate'
 'System.RevisedDate'
 'System.IterationId'
 'System.IterationPath'
 'System.IterationLevel1'
 'System.WorkItemType'
 'System.State'
 'System.Reason'
 'System.AssignedTo'
 'System.CreatedDate'
 'System.CreatedBy'
 'System.ChangedDate'
 'System.ChangedBy'
 'System.AuthorizedAs'
 'System.PersonId'
 'System.Watermark'
 'System.CommentCount'
 'System.Title'
 'System.BoardColumn'
 'System.BoardColumnDone'
 'Microsoft.VSTS.Common.StateChangeDate'
 'Microsoft.VSTS.Common.ActivatedDate'
 'Microsoft.VSTS.Common.ActivatedBy'
 'Microsoft.VSTS.Common.ResolvedDate'
 'Microsoft.VSTS.Common.ResolvedBy'
 'Microsoft.VSTS.Common.ClosedDate'
 'Microsoft.VSTS.Common.ClosedBy'
 'Microsoft.VSTS.Common.Priority'
 'Microsoft.VSTS.Common.ValueArea'
 'WEF_FBD2D976074B482F829B5958F33303A4_System.ExtensionMarker'
 'WEF_FBD2D976074B482F829B5958F33303A4_Kanban.Column'
 'WEF_FBD2D976074B482F829B5958F33303A4_Kanban.Column.Done'
 'WEF_B48DD1C291164BEBA44336D79AA87179_System.ExtensionMarker'
 'WEF_B48DD1C291164BEBA44336D79AA87179_Kanban.Column'
 'WEF_B48DD1C291164BEBA44336D79AA87179_Kanban.Column.Done'
 'System.Parent']

class ResponseException(Exception):
    pass


def get_client(personal_access_token, base_url):

    config = Configuration(base_url)
    VERSION = "6.0.0b2"
    config.add_user_agent('azure-devops/{}'.format(VERSION))
    config.additional_headers = {}

    creds = BasicAuthentication('', personal_access_token)

    client = ServiceClient(creds, config=config)

    return client

organisation = 'swansea-university'
project = 'Swansea%20Academy%20of%20Advanced%20Computing'

client = get_client(personal_access_token, f'https://dev.azure.com/{organisation}')

def send(http_method, url, headers, content=None):
    """Prepare and send request object according to configuration.
    :param str http_method: GET/POST
    :param str url: The request target url
    :param dict headers: Any headers to add to the request.
    :param content: Any body data to add to the request.
    """
    request = ClientRequest(method=http_method, url=url)

    response = client.send(request=request, headers=headers, content=content)

    if not response.ok:
        raise ResponseException(f'Response Error <{response.status_code}> : \n{response.content}')
    else:
        return response

def send_json(http_method, url, headers, content=None):
    response = send(http_method, url, headers, content=None)

    return response.json()

def default_headers():
    return {'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json;api-version=6.0-preview.2', 'X-TFS-FedAuthRedirect': 'Suppress', 'X-VSS-ForceMsaPassThrough': 'true', 'X-TFS-Session': 'd3ce4044-af1c-45a2-8ef5-e1854f30bd6e'}

def get(url):
    headers = default_headers()

    return send_json('GET', url=url, headers=headers)

def get_teams():
    return get(f'https://dev.azure.com/{organisation}/_apis/projects/{project}/teams')['value']

def query(q):
    response = send('POST',
                    url=f'https://dev.azure.com/{organisation}/_apis/wit/wiql',
                    headers = default_headers(),
                    content = {"query" : q})

    ids = [ item['id'] for item in response.json()['workItems']]

    work_items = get_work_items_by_id(ids)

    return work_items

def get_work_items_by_id(ids):
    all_items = []

    # ensure uniqueness of ids
    ids = list(set(ids))

    # limit the chunk sizes, otherwise the API breaks
    chunk_size = 100
    for i in range(0, len(ids), chunk_size):
    # For item i in a range that is a length of l,
        chunk = ids[i:i+chunk_size]
        items = get_work_items_by_id_unchunked(chunk)
        all_items.extend(items)

    return all_items

def get_work_items_by_id_unchunked(ids):

    ids = [str(id) for id in ids]

    ids = ",".join(ids)

    url = f'https://dev.azure.com/swansea-university/_apis/wit/workItems?ids={ids}&$expand=Relations&errorPolicy=Omit'

    return get(url)['value']

def epics_by_team(team):
    results = query("SELECT * FROM workitems WHERE [System.WorkItemType] = 'EPIC' AND [System.AreaPath] = 'Swansea Academy of Advanced Computing\\"+ team + "'")

    return results

teams = get_teams()

# Add epics to teams
for team in teams:
  team_name = team['name']
  print(team_name)
  try:
      team['children'] = epics_by_team(team['name'])
  except:
      print(f'Error finding epics for {team_name}')
      team['children'] = []



# look for relations or children
# if relations, add to fetchable ids, if children, continue walking looking for fetchable ids
# fetch all child items in dict
# check if any unfetched relations in child items... (recur)

def id_from_relation(relation):
    return int(relation['url'].split('/')[-1])

def find_missing_ids(items):
    ids = set()
    for item in items:
        if 'children' in item:
            # item has had children added, walk the children
            new_ids = find_missing_ids(item['children'])
        elif 'relations' in item.keys():
            # item has a relation, add the id
            new_ids = [ id_from_relation(relation)
                       for relation in item['relations']
                        if relation['rel'] == 'System.LinkTypes.Hierarchy-Forward'
                        ]
        else:
            new_ids = []

        ids.update(new_ids)

    return ids

def add_missing_children(items, wi_dict):
    for item in items:
        if 'children' in item:
           # item has had children added, walk the children
            add_missing_children(item['children'], wi_dict)
        elif 'relations' in item:
            # item has a relation, add the id
            item['children'] = [
                wi_dict[id_from_relation(relation)]
                for relation in item['relations']
                if relation['rel'] == 'System.LinkTypes.Hierarchy-Forward'
            ]

def org_summary(items, state_p = lambda x: True, level=0):
    for idx, item in enumerate(items):
        assigned_to = ''

        if 'fields' in item:
            label = item['fields']['System.Title']
            wi_type = item['fields']['System.WorkItemType']
            wi_state = item['fields']['System.State']
            if 'System.AssignedTo' in item['fields']:
                assigned_to = ' assigned-to: ' + item['fields']['System.AssignedTo']
        elif 'name' in item:
            label = item['name']
            wi_type = 'TEAM'
            wi_state = '?'
        if state_p(wi_state):
            print('*'*level + str(idx) + ')' + label + ' (' + str(item['id']) + ') [' + wi_type + '/' + wi_state + ']' + assigned_to)
        if 'children' in item:
            # item has had children added, walk the children
            org_summary(item['children'], state_p, level + 1)

def print_summary(items, state_p = lambda x: True, level=0):
    for idx, item in enumerate(items):
        if 'fields' in item:
            label = item['fields']['System.Title']
            wi_type = item['fields']['System.WorkItemType']
            wi_state = item['fields']['System.State']
        elif 'name' in item:
            label = item['name']
            wi_type = 'TEAM'
            wi_state = '?'
        if state_p(wi_state):
            print('-'*level + '> ' + str(idx) + ')' + label + ' (' + str(item['id']) + ') [' + wi_type + '/' + wi_state + ']')
        if 'children' in item:
            # item has had children added, walk the children
            print_summary(item['children'], state_p, level + 1)

def fill_in_missing_ids(teams):
    missing_ids = find_missing_ids(teams)

    if len(missing_ids) > 0:
        work_items = get_work_items_by_id(missing_ids)
        work_items_dict = { item['id'] : item for item in work_items }
        add_missing_children(teams, work_items_dict)

        fill_in_missing_ids(teams)

fill_in_missing_ids(teams)

print_summary(teams, state_p = lambda x : x != 'Closed')
