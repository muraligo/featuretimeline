#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 08 11:28:41 2020

@author: mugopala

Various entities common to many projects
"""

import base64
from .helpers import jsonloads

# vault_name = 'vault-opam-sandbox'


def get_oci_secret_by_name(secretname, apihandler, lggr, ssvcconfig, version=None, opcreqid=None):
    url1 = "{base_url}/{api_version}/secrets?name={secret_name}&compartmentId={compartment_id}".format(
        base_url=ssvcconfig['manage_url'],
        api_version=ssvcconfig['manage_apiversion'],
        compartment_id=ssvcconfig['compartmentId'].replace(":", "%3A"),
        secret_name=secretname
    )
#    print(url1)

    # TODO add opc request id as a header parameter if provided

    result1 = apihandler.handle_get(url1)
    if result1 is None:
        return None

    lggr.debug('Result of {url} is {result}'.format(url=url1, result=result1))
    print('Result of {url} is {result}'.format(url=url1, result=result1))
 #   print(result1.text)
    if result1.status_code != 200:
        # TODO Do more with errors?
        return None

    # TODO if opc request id is provided, verify from the response header that it is the same

    secretssummaries = result1.json()
#    print(secretssummaries)

    secretssummary = None
    if len(secretssummaries) != 1:
        # TODO should we raise error or just take the first one as casing could return multiple
        secretssummary = secretssummaries[0]
    else:
        secretssummary = secretssummaries[0]
    secretid = secretssummary['id']

    _coreurl = "{base_url}/{api_version}/secretbundles/{secret_id}".format(
        base_url=ssvcconfig['bundle_url'],
        api_version=ssvcconfig['bundle_apiversion'],
        secret_id=secretid
    )
    # add version as a query parameter if provided
    url2 = _coreurl if version is None else "{coreurl}?versionNumber={secret_version}".format(
        coreurl=_coreurl,
        secret_version=version
    )
    result2 = apihandler.handle_get(url2)
    if result2 is None:
        return None

    lggr.debug('Result of {url} is {result}'.format(url=url2, result=result2))
    print('Result of {url} is {result}'.format(url=url2, result=result2))
#    print(result2.text)
    if result2.status_code != 200:
        # TODO Do more with errors?
        return None

    secretbundle = result2.json()
    # Ensure that besides the REQUIRED fields, secretBundleContent is returned
    if 'secretBundleContent' not in secretbundle:
        raise ValueError('Secret not returned from API call')
    secretcontstruct = secretbundle['secretBundleContent']
    if secretcontstruct['contentType'] != 'BASE64':
        raise ValueError('Invalid format secret returned from API call')
    secretcontent = None
    # Do a base64 decode of secretcontstruct['content'] into secretcontent.
    # the TypeError thrown is not trapped and allowed to pass to the caller
    secretcontent = base64.b64decode(secretcontstruct['content'])
    return secretcontent


def get_secrets_in_compartment(apihandler, ssvcconfig):
    url1 = "{base_url}/{api_version}/secrets?compartmentId={compartment_id}".format(
        base_url=ssvcconfig['manage_url'],
        api_version=ssvcconfig['manage_apiversion'],
        compartment_id=ssvcconfig['compartmentId'].replace(":", "%3A")
    )
    print(url1)

    result1 = apihandler.handle_get(url1)
    # TODO Handle all errors.
    print(result1.text)

# Should ideally do a ListSecret by compartmentId, name, and vaultId as query params.
# Then turn around and retrieve Bundle details by id and version of CURRENT
# SecretBundle Reference
# The contents of the secret, properties of the secret (and secret version), 
# and user-provided contextual metadata for the secret.
# Attributes:
#     secretId      - (Required: yes, Type: string, The OCID of the secret.)
#     timeCreated   - (Required: no, Type: string, The time when the secret bundle was created.)
#     versionNumber - (Required: yes, Type: integer, The version number of the secret.)
#     versionName   - (Required: no, Type: string, The name of the secret version.)
#                       (Labels are unique across the different versions of a particular secret.)
#     secretBundleContent   - (Required: no, Type: SecretBundleContentDetails, Content details - see below.)
#     timeOfDeletion - (Required: no, Type: string, An optional property indicating when to delete the secret version, expressed in RFC 3339 timestamp format.)
#                       Example: 2019-04-03T21:10:29.600Z
#     timeOfExpiry  - (Required: no, Type: string, An optional property indicating when the secret version will expire, expressed in RFC 3339 timestamp format.)
#                       Example: 2019-04-03T21:10:29.600Z
#     stages        - (Required: no, Type: [string, ...], A list of possible rotation states for the secret version.)
#     metadata      - (Required: no, Type: object, Customer-provided contextual metadata for the secret.)
#
# Example:
# {
#   "secretId" : "ocid1.vaultsecret.oc1.iad.exampleaz5qacpqadubrc4wwugrqmw5dnyzvcxwzds6er5enn2oamexample",
#   "timeCreated" : "2020-03-18T16:51:38.851Z",
#   "versionNumber" : 1,
#   "versionName" : null,
#   "secretBundleContent" : {
#     "contentType" : "BASE64",
#     "content" : "aGVsbG8h"
#   },
#   "timeOfDeletion" : null,
#   "timeOfExpiry" : null,
#   "stages" : [ "CURRENT", "LATEST" ],
#   "metadata" : null
# }
#
# SecretBundleContent Details
#   contentType     - (Required: yes, Type: string, The encoding type of the content.)
#                       (Allowed values are: BASE64.)
#   content         - (Required: depends on content type - yes for BASE64, Type: string, 
#                       The actual secret material.)
#
#
# Secret Reference
# The details of the secret. Secret details do not contain the contents of the secret itself.
# Attributes
#   compartmentId   - (Required: yes, Type: string, The OCID of the compartment where you want to create the secret.)
#   currentVersionNumber - (Required: no, Type: integer, The version number of the secret version that's currently in use.)
#   definedTags     - (Required: no, Type: object, Defined tags for this resource.)
#                       (Each key is predefined and scoped to a namespace. For more information, see Resource Tags.)
#                       (Example: {"Operations": {"CostCenter": "42"}})
#   description     - (Required: no, Type: string, A brief description of the secret.)
#                       (NOTE: Avoid entering confidential information.)
#   freeformTags    - (Required: no, Type: object, Free-form tags for this resource.)
#                       (Each tag is a simple key-value pair with no predefined name, type, or namespace.)
#                       (For more information, see Resource Tags.)
#                       (Example: {"Department": "Finance"})
#   id              - (Required: yes, Type: string, The OCID of the secret.)
#   keyId           - (Required: no, Type: string, The OCID of the master encryption key that is used to encrypt the secret.)
#   lifecycleDetails - (Required: no, Type: string, Min Length: 1, Max Length: 4000, 
#                       Additional information about the current lifecycle state of the secret.)
#   lifecycleState  - (Required: yes, Type: string, The current lifecycle state of the secret.)
#                       (Allowed values are: CREATING, ACTIVE, UPDATING, DELETING, DELETED, 
#                        SCHEDULING_DELETION, PENDING_DELETION, CANCELLING_DELETION, FAILED)
#   metadata        - (Required: no, Type: object, Additional metadata that you can use to provide context 
#                       about how to use the secret or during rotation or other administrative tasks.)
#                       (For example, for a secret that you use to connect to a database, 
#                        the additional metadata might specify the connection endpoint 
#                        and the connection string.)
#                       (Provide additional metadata as key-value pairs.)
#   secretName      - (Required: yes, Type: string, The user-friendly name of the secret.)
#                       (NOTE: Avoid entering confidential information.)
#   secretRules     - (Required: no, Type: [SecretRule, ...], A list of rules that control how the secret is used and managed.)
#                        (See below for structure of SecretRule.)
#   timeCreated     - (Required: yes, Type: string, A property indicating when the secret was created, expressed in RFC 3339 timestamp format.)
#                       (Example: 2019-04-03T21:10:29.600Z)
#   timeOfCurrentVersionExpiry - (Required: no, Type: string, An optional property indicating when the current secret version will expire, expressed in RFC 3339 timestamp format.)
#                       (Example: 2019-04-03T21:10:29.600Z
#   timeOfDeletion  - (Required: no, Type: string, An optional property indicating when to delete the secret, expressed in RFC 3339 timestamp format.)
#   vaultId         - (Required: yes, Type: string, The OCID of the vault where the secret exists.)
#
# Example
# {
#   "compartmentId" : "ocid1.tenancy.oc1..exampleah7zkvaffv26pzyauoe2zbncvbqvhvsudmlpe557wakiofexample”,
#   "currentVersionNumber" : 1,
#   "definedTags" : { },
#   "description" : "example secret description",
#   "freeformTags" : { },
#   "id" : "ocid1.vaultsecret.oc1.iad.exampleaz5qacpqadubrc4wwugrqmw5dnyzvcxwzds6er5enn2oamexample”,
#   "keyId" : "ocid1.key.oc1.iad.exampleyaaeuk.abuwcvbrswr2nbvrraqomsmhopc74rlqupwyv3byhikd4577rrky7example”,
#   "lifecycleDetails" : null,
#   "lifecycleState" : "ACTIVE",
#   "metadata" : null,
#   "secretName" : "exampleSecret",
#   "secretRules" : [ {
#     "ruleType" : "SECRET_EXPIRY_RULE",
#     "secretVersionExpiryInterval" : "P30D",
#     "timeOfAbsoluteExpiry" : "2021-03-18T22:00:00.000Z",
#     "isSecretContentRetrievalBlockedOnExpiry" : false
#   }, {
#     "ruleType" : "SECRET_REUSE_RULE",
#     "isEnforcedOnDeletedSecretVersions" : true
#   } ],
#   "timeCreated" : "2020-03-18T16:51:38.851Z",
#   "timeOfCurrentVersionExpiry" : null,
#   "timeOfDeletion" : null,
#   "vaultId" : "ocid1.vault.oc1.iad.exampleyaaeuk.examplesuxtdqxczlvygwk4ouq2mhzr223g4o2ojs4o4q4ghmt6rlexample”
# }
#
# SecretRule Reference
#   ruleType        - (Required: yes, Type: string, The type of rule, which either controls 
#                       when the secret contents expire or whether they can be reused.)
#                       (Allowed values are: SECRET_EXPIRY_RULE, SECRET_REUSE_RULE.)
# SecretExpiryRule Reference
#   secretVersionExpiryInterval - (Required: no, Type: string, A property indicating how long the secret contents will be considered valid, expressed in ISO 8601 format.)
#                       (The secret needs to be updated when the secret content expires. No enforcement mechanism exists at this time, 
#                        but audit logs record the expiration on the appropriate date, according to the time interval specified in the rule. 
#                        The timer resets after you update the secret contents. 
#                        The minimum value is 1 day and the maximum value is 90 days for this property. 
#                        Currently, only intervals expressed in days are supported.)
#                       (For example, pass P3D to have the secret version expire every 3 days.)
#   timeOfAbsoluteExpiry - (Required: no, Type: string, An optional property indicating the absolute time when this secret will expire, expressed in RFC 3339 timestamp format.)
#                       (The minimum number of days from current time is 1 day and the maximum number of days from current time is 365 days.)
#                       (Example: 2019-04-03T21:10:29.600Z.)
#   isSecretContentRetrievalBlockedOnExpiry - (Required: no, Type: boolean, A property indicating whether to block retrieval of the secret content, on expiry.)
#                       (The default is false. If the secret has already expired and you would like to retrieve the secret contents, you need to edit the secret rule 
#                        to disable this property, to allow reading the secret content.)
# SecretReuseRule Reference
#   isEnforcedOnDeletedSecretVersions - (Required: no, Type: boolean, A property indicating whether the rule is applied even if the secret version with the content you are trying to reuse was deleted.)


