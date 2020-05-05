import base64
import email.utils
import hashlib

# pip install httpsig_cffi requests six
# httpsig_cffi v15.0.0
#   six v1.12.0
#   cryptography v2.6.1
#     asn1crypto v0.24.0
#   cffi v1.12.2
#     pycparser v2.19
import httpsig_cffi.sign
import requests
import six
import json
from .helpers import file_reader

class SignedRequestAuth(requests.auth.AuthBase):
    """A requests auth instance that can be reused across requests"""
    generic_headers = [
        "date",
        "(request-target)",
        "host"
    ]
    body_headers = [
        "content-length",
        "content-type",
        "x-content-sha256",
    ]
    required_headers = {
        "get": generic_headers,
        "head": generic_headers,
        "delete": generic_headers,
        "put": generic_headers + body_headers,
        "post": generic_headers + body_headers
    }

    def __init__(self, key_id, private_key):
        # Build a httpsig_cffi.requests_auth.HTTPSignatureAuth for each
        # HTTP method's required headers
        self.signers = {}
        for method, headers in six.iteritems(self.required_headers):
            signer = httpsig_cffi.sign.HeaderSigner(
                key_id=key_id, secret=private_key,
                algorithm="rsa-sha256", headers=headers[:])
            use_host = "host" in headers
            self.signers[method] = (signer, use_host)

    def inject_missing_headers(self, request, sign_body):
        # Inject date, content-type, and host if missing
        request.headers.setdefault(
            "date", email.utils.formatdate(usegmt=True))
        if 'content-type' not in request.headers:
            if isinstance(request.body, bytes):
                request.headers.setdefault("content-type", "application/octet-stream")
            else:
                request.headers.setdefault("content-type", "application/json")
        request.headers.setdefault(
            "host", six.moves.urllib.parse.urlparse(request.url).netloc)

        # Requests with a body need to send content-type,
        # content-length, and x-content-sha256
        if sign_body:
            body = request.body or ""
            if "x-content-sha256" not in request.headers:
                if 'application/json' == request.headers['content-type']:
                    m = hashlib.sha256(body.encode("utf-8"))
                else:
                    m = hashlib.sha256(body)
                base64digest = base64.b64encode(m.digest())
                base64string = base64digest.decode("utf-8")
                request.headers["x-content-sha256"] = base64string
            request.headers.setdefault("content-length", len(body))

    def __call__(self, request):
        verb = request.method.lower()
        # nothing to sign for options
        if verb == "options":
            return request
        signer, use_host = self.signers.get(verb, (None, None))
        if signer is None:
            raise ValueError(
                "Don't know how to sign request verb {}".format(verb))

        # Inject body headers for put/post requests, date for all requests
        sign_body = verb in ["put", "post"]
        self.inject_missing_headers(request, sign_body=sign_body)

        if use_host:
            host = six.moves.urllib.parse.urlparse(request.url).netloc
        else:
            host = None

        signed_headers = signer.sign(
            request.headers, host=host,
            method=request.method, path=request.path_url)
        request.headers.update(signed_headers)
        return request


class OciApiHandler:

    def __init__(self, ocicfgfile, basepath=None):
        _fullpath = ocicfgfile if basepath is None else '{}/{}'.format(basepath, ocicfgfile)
        jshash = json.loads(file_reader(_fullpath))
        if jshash and len(jshash) > 0:
            _tenantocid = jshash['TENANTOCID']
            _userocid = jshash['USEROCID']
            _fingerprint = jshash['FINGERPRINT']
            _keyfilepath = jshash['KEYFILE']
            self.api_key = "/".join([_tenantocid, _userocid, _fingerprint])
            with open(_keyfilepath) as f:
                self.private_key = f.read().strip()
            self.auth = SignedRequestAuth(self.api_key, self.private_key)

    def handle_get(self, rqurl, rqhdrs=None):
        if rqhdrs is None:
            rqhdrs = {}
        if 'content-type' not in rqhdrs:
            rqhdrs['content-type'] = 'application/json'
        if 'date' not in rqhdrs:
            rqhdrs['date'] = email.utils.formatdate(usegmt=True)
        response = requests.get(rqurl, auth=self.auth, headers=rqhdrs)
        if response:
            print(response.request.headers["Authorization"])
        return response

    def handle_put(self, rqurl, rqbody, rqlen, rqhdrs=None):
        if rqhdrs is None:
            rqhdrs = {}
        # content-type defaults to octet stream
        if 'content-length' not in rqhdrs:
            rqhdrs['content-length'] = "%d" % rqlen
        if 'date' not in rqhdrs:
            rqhdrs['date'] = email.utils.formatdate(usegmt=True)
        response = requests.put(rqurl, rqbody, auth=self.auth, headers=rqhdrs)
        if response:
            print(response.request.headers["Authorization"])
        return response



