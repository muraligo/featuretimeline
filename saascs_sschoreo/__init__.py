#

import os
from . import helpers, task_consts, task_helper, service_helper
from .log import setup_logging
from .jira_lib import initforenv, Jira
from .oci_helpers import OciApiHandler


print(f'Invoking __init__.py for {__name__}')

# Maps environment name to the environment config file names
environments = {
    'local': 'local_dev',
#    'dev': Development,
    'integ': 'integration',
    'prod': 'production'
}

app_env = os.getenv('SAASCS_CHOREO_ENV')
appconfig = helpers.from_envvar('SAASCS_CHOREO_CONFIG', silent=True)
databasepath = None
if not appconfig and app_env == 'local':
    appconfig = dict()
    appconfig['BASEPATH'] = '/users/mugopala/AllDocs/dev/regionbuild/saascs_choreo/data'

databasepath = appconfig['BASEPATH']
cfgfilename = environments[app_env] + '.json'
confbasepath = databasepath + '/conf'
print(f'Values for ENV {app_env} and config file {cfgfilename}')
_appcfg2 = helpers.from_json(cfgfilename, confbasepath)
print(_appcfg2)
for (cfgit2key, cfgit2val) in _appcfg2.items():
    if cfgit2key not in appconfig:
        appconfig[cfgit2key] = cfgit2val

applogger = setup_logging(appconfig['LOGGING'])

initforenv(appconfig['ENVNAME'], appconfig['JIRA_CONFIG'], databasepath, applogger)
# jirahelper = Jira('gbucs')
# jirahelper.getrequest('project', 's')


def print_children0(svcarr, indnt2):
    for svc2 in svcarr:
        strind = ' ' * indnt2
        print("%s%s" % (strind, svc2))
        if len(svc2.children) > 0:
            indnt2 = indnt2 + 2
            print_children0(svc2.children, indnt2)
            indnt2 = indnt2 - 2


def print_children(svcarr):
    for svc2 in svcarr:
        print("  %s" % (svc2))
        if len(svc2.children) > 0:
            print_children(svc2.children)


def load_print_services():
    services = service_helper.load_services(applogger, basepath=appconfig['BASEPATH'])
    # print(services)
    for svckey in services:
        svc1 = services[svckey]
        print("%s:%s" % (svckey, svc1))
        # indent = 0
        if len(svc1.children) > 0:
            print_children(svc1.children)
            # indent = indent + 2
            # print_children0(svc1.children, indent)
            # indent = indent - 2
    return services


ossconfig = appconfig['OSS_CONFIG']


def list_oci_oss_namespace():
    url = "https://objectstorage.us-phoenix-1.oraclecloud.com/n/?compartmentId={compartment_id}".format(
        compartment_id="ocid1.tenancy.oc1..aaaaaaaaamuhda4xcynzumstqiwxbx5d2mkmeqflyfnwsta6gn4g7ofmnfkq".replace(":", "%3A")
    )

    result = myapihandler.handle_get(url)
    print(result)
    print(result.text)


def get_oci_oss_file_data():
    url = "{base_url}/n/{csrb_namespace}/b/mitch-7262/o/testscript?compartmentId={compartment_id}".format(
        base_url=ossconfig['base_url'],
        csrb_namespace=ossconfig['namespace'],
        compartment_id=ossconfig['compartmentId'].replace(":", "%3A")
    )

    result = myapihandler.handle_get(url)
    print(result)
    print(result.text)
    return result.text



def try_put_file_in_ocioss():
    # auto_region_build/
    url = "{base_url}/n/{csrb_namespace}/b/mitch-7262/o/?compartmentId={compartment_id}".format(
        base_url=ossconfig['base_url'],
        csrb_namespace=ossconfig['namespace'],
        compartment_id=ossconfig['compartmentId'].replace(":", "%3A")
    )

    result = myapihandler.handle_get(url)
    print(result)
    print(result.text)

    ossobjs = helpers.jsonloads(result.text)
    if len(ossobjs['objects']) == 0:
        url3 = "{base_url}/n/{csrb_namespace}/b/mitch-7262/o/testscript?compartmentId={compartment_id}".format(
            base_url=ossconfig['base_url'],
            csrb_namespace=ossconfig['namespace'],
            compartment_id=ossconfig['compartmentId'].replace(":", "%3A")
        )
        scrptpath = './tests/osstestscript.sh' if databasepath is None else '{}/tests/osstestscript.sh'.format(databasepath)
        with open(scrptpath, 'rb') as binscrptf:
            datatoput = binscrptf.read()
        print(len(datatoput))
        hdrs3 = {}
        hdrs3['content-type'] = 'application/octet-stream'
        result3 = myapihandler.handle_put(url3, datatoput, len(datatoput))
        print(result3)
        result2 = myapihandler.handle_get(url)
        print(result2)
        print(result2.text)
        return result2.text
    else:
        return result.text


myapihandler = OciApiHandler('/Users/mugopala/.oci/gbucs_nopw_devcorp_config.json')
tasksbystage = task_helper.cs_load_tasks(applogger, myapihandler, appconfig, basepath=appconfig['BASEPATH'])
currstg = task_consts.SaasCsTaskStage.PRIMORDIAL
print("%s" % currstg)
task_helper.print_task(tasksbystage[currstg])
task_helper.choreograph_tasks(applogger, tasksbystage, appconfig)

# TODO Comment all this when testing above
# load_print_services()
# list_oci_oss_namespace()
# bucket_contents = try_put_file_in_ocioss()
# file_contents = get_oci_oss_file_data()



