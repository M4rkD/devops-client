import comms

personal_access_token = 'iywk3uook2xwvsmjhoztcb7qvka4qrpjvdtjicgaif3ofy5x4gbq'



organisation = 'swansea-university'
project = 'Swansea%20Academy%20of%20Advanced%20Computing'

client = comms.get_client(personal_access_token, f'https://dev.azure.com/{organisation}')


def get_teams():
    """
    Fetch a list of teams
    """
    return comms.get(f'https://dev.azure.com/{organisation}/_apis/projects/{project}/teams')['value']

def query(q):
    """
    Fetch list of work items given a wiql query
    """
    response = comms.send('POST',
                    url=f'https://dev.azure.com/{organisation}/_apis/wit/wiql',
                    headers = default_headers(),
                    content = {"query" : q})

    ids = [ item['id'] for item in response.json()['workItems']]

    work_items = get_work_items_by_id(ids)

    return work_items

def get_work_items_by_id(ids):
    """
    Get work items by id (in chunks)
    """
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
    """
    Get work items by id (without chunking)
    """

    ids = [str(id) for id in ids]

    ids = ",".join(ids)

    url = f'https://dev.azure.com/swansea-university/_apis/wit/workItems?ids={ids}&$expand=Relations&errorPolicy=Omit'

    return comms.get(url)['value']

def epics_by_team(team):
    """
    Fetch all epics for a given team
    """
    results = query("SELECT * FROM workitems WHERE [System.WorkItemType] = 'EPIC' AND [System.AreaPath] = 'Swansea Academy of Advanced Computing\\"+ team + "'")

    return results

def id_from_relation(relation):
    """
    Extract work item id from a relation (by splitting url)
    """
    return int(relation['url'].split('/')[-1])

def find_missing_ids(items):
    """
    Walk the `items` tree looking for a relations key without a children key, and collect the ids of the missing 'children' entries by reading the list in the 'relations' key.
    Fetch only items of type Hierarchy-Forward
    :param dict items: tree-like data structure (dicts and lists), in which identity of children is specified with the 'relations' key, and data of children is stored in children.
    the ids of child work items.
    :param dict wi_dict: a key key-value lookup structure. Keys are work item ids and values are the work item data.
    """
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
    """
    Walk the `items` tree looking for a relations key without a children key, and populate the children list based on the relations list.
    the children work items have not been populated). Populate this list form `wi_dict`
    :param dict items: tree-like data structure (dicts and lists), in which identity of children is specified with the 'relations' key, and data of children is stored in children.
    the ids of child work items.
    :param dict wi_dict: a key key-value lookup structure. Keys are work item ids and values are the work item data.
    """
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
    """
    Walk the `items` tree printing the results based on a state predicate function `state_p`
    :param dict items: tree-like data structure (dicts and lists)
    :param function state_p: optional predicate function to filter outputs
    """
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

def fill_in_missing_ids(items):
    """
    Recur on the items tree structure, looking for missing ids.
    Whilst missing ids are found, fetch their data.

    :param dict items: tree-like data structure (dicts and lists)
    :param function state_p: optional predicate function to filter outputs
    """
    missing_ids = find_missing_ids(items)

    if len(missing_ids) > 0:
        work_items = get_work_items_by_id(missing_ids)
        work_items_dict = { item['id'] : item for item in work_items }
        add_missing_children(items, work_items_dict)

        fill_in_missing_ids(items)

# Fetch epics for  teams
teams = get_teams()

for team in teams:
  team_name = team['name']
  print(team_name)
  try:
      team['children'] = epics_by_team(team['name'])
  except:
      print(f'Error finding epics for {team_name}')
      team['children'] = []


# Iterate list, recursively following (and adding) children fields to work items,
# based on the ids found in their relation fields.
fill_in_missing_ids(teams)

# resursively print list
print_summary(teams, state_p = lambda x : x != 'Closed')
