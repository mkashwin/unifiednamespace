import requests

# Database Credentials
# FIXME Need to read these secrets from Kubernetes
uri             = "" #TBD
userName        = "" #TBD
password        = "" #TBD
#
#    with open("/var/openfaas/secrets/timescaledb-key") as f:
#        password = f.read().strip()
#Extract the topic 
topic=""
#Extract the msg in JSON format
msg=""

def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """

    return request

