import logging
log = logging.getLogger(__name__)


def get_creds(conf):
    d = {}
    d['username'] = conf.get("environment", "OS_USERNAME")
    d['api_key'] = conf.get("environment", "OS_PASSWORD")
    d['auth_url'] = conf.get("environment", "OS_AUTH_URL")
    d['project_id'] = conf.get("environment", "OS_TENANT_NAME")
    return d

