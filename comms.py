from msrest import Configuration
from msrest.authentication import BasicAuthentication
from msrest.service_client import ServiceClient


class ResponseException(Exception):
    pass

def default_headers():
    return {'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json;api-version=6.0-preview.2', 'X-TFS-FedAuthRedirect': 'Suppress', 'X-VSS-ForceMsaPassThrough': 'true', 'X-TFS-Session': 'd3ce4044-af1c-45a2-8ef5-e1854f30bd6e'}

def get_client(personal_access_token, base_url):
    """Get a client for interacting with devops
    :param str http_method: GET/POST
    :param str url: The request target url
    :param dict headers: Any headers to add to the request.
    :param content: Any body data to add to the request.
    """

    config = Configuration(base_url)
    VERSION = "6.0.0b2"
    config.add_user_agent('azure-devops/{}'.format(VERSION))
    config.additional_headers = {}

    creds = BasicAuthentication('', personal_access_token)

    client = ServiceClient(creds, config=config)

    return client

def send(client, http_method, url, headers, content=None):
    """Prepare and send request object to devops according to configuration.
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

def send_json(client, http_method, url, headers, content=None):
    """Wraps send method, converting response to json
    :param ClientRequest client: the request
    :param str http_method: GET/POST
    :param str url: the url to get
    :param dict headers: http headers
    :param dict content: http data
    """
    response = send(client, http_method, url, headers, content=None)

    return response.json()

def get(client, url):
    """Uses client to query url using GET with default headers
    :param str client: a ClientRequest object
    """
    headers = default_headers()

    return send_json(client, 'GET', url=url, headers=headers)
