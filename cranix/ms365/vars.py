# -*- coding: utf-8 -*-

# Copyright (c) 2026 Peter Varkoly <pvarkoly@cephalix.eu> All rights reserved.

token_file = '/opt/cranix-ms365/token'
config_file = '/opt/cranix-ms365/config'

MS365_DIR = '/var/adm/cranix/ms365'
USERIDS_DIR = MS365_DIR + '/userids'
GROUPIDS_DIR = MS365_DIR + '/groupids'
FAILED_DIR = MS365_DIR + '/failed'

msuser = {
    "accountEnabled": True,
    "userprincipalname": "##UPN##",
    "jobTitle": "Schüler",
    "mailnickname": "##UID##",
    "displayName": "##GIVENNAME## ##SURNAME##",
    "givenName": "##GIVENNAME##",
    "surName": "##SURNAME##",
    "state": "##STATE##",
    "usageLocation": "##USAGELOCATION##",
    "passwordPolicies": "DisablePasswordExpiration, DisableStrongPassword",
    "country": "##COUNTRY##",
    "city": "##CITY##",
    "userType": "Member",
    "passwordProfile": {
        "password": "##PW##",
        "forceChangePasswordNextSignIn": False,
        "forceChangePasswordNextSignInWithMfa": False
    }
}

msgroup = {
    "displayName": '##NAME##',
    "mailNickname": '##NAME##',
    "description": '##DESC##',
    "visibility": "Private",
    "groupTypes": ["Unified"],
    "mailEnabled": "true",
    "locale": "de-DE",
    "securityEnabled": "false",
}

msteam = {
    "template@odata.bind": "https://graph.microsoft.com/beta/teamsTemplates('educationClass')",
    "displayName": '##NAME##',
    "description": '##DESC##',
    "members": [
        {
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": [
                "owner"
            ],
            "user@odata.bind": "https://graph.microsoft.com/beta/users('##ADMINID##')"
        }
    ]
}