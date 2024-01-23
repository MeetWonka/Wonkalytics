import logging

def extract_auth_info_pl_tags(auth_info : dict) -> (str, str, str):
    '''Returns strings for the tenant, username and usermail from a model_dump/prompt_variables.'''

    # Authinfo and clientprincipal is optional and could be None
    if auth_info is None:
        logging.info("There was no authinfo present on the request.")
        return None, None, None
    
    if not 'clientPrincipal' in auth_info or auth_info['clientPrincipal'] is None:
        logging.warning('There was authinfo present on the request but the required keys were not found. See resources/ExampleAuthInfo.js for an example of what the authinfo structure should look like (default azure auth structure).')
        return None, None, None
    
    # Catch malformed authinfo so it does not crash the server response
    if not 'claims' in auth_info["clientPrincipal"]:
        logging.error('Received incomplete/invalid auth_info (missing clientPrincipal or claims):')
        logging.error(auth_info)
        # Let's not raise here yet, so we don't break some production code
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