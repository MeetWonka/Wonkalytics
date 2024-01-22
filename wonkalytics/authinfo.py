import logging

def extract_auth_info_pl_tags(auth_info : dict) -> (str, str, str):
    '''Returns strings for the tenant, username and usermail from a model_dump/prompt_variables.'''

    # Authinfo and clientprincipal is optional and could be None
    if auth_info is None:
        return 'None', 'None', 'None'
    
    if not 'clientPrincipal' in auth_info or auth_info['clientPrincipal'] is None:
        return 'None', 'None', 'None'
    
    # Catch malformed authinfo so it does not crash the server response
    if not 'claims' in auth_info["clientPrincipal"]:
        logging.error('Received incomplete/invalid auth_info (missing clientPrincipal or claims):')
        logging.error(auth_info)
        return 'Invalid', 'Invalid', 'Invalid'

    # Extract auth object
    client_principal = auth_info['clientPrincipal']

    # Find relevant claims in the claims array
    tenantid_claim = next((claim for claim in client_principal['claims'] if claim['typ'] == 'http://schemas.microsoft.com/identity/claims/tenantid'), {'val': 'None'})
    name_claim = next((claim for claim in client_principal['claims'] if claim['typ'] == 'name'), {'val': 'None'})
    
    # Extract strings
    tenantid = tenantid_claim['val']
    user_name = name_claim['val']
    user_mail = client_principal['userDetails']

    return tenantid, user_name, user_mail