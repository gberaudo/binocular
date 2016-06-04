import subprocess
from bottle import run, request, response, route, static_file
from multiprocessing import Process, get_logger

import hashlib
import hmac
import os
import configparser


config = configparser.ConfigParser()
config.read('config.ini')
REPO = config.get('main', 'allowed')
EVENT_AUTH = config.get('main', 'event_auth')
EVENT_SECRET = config.get('main', 'event_secret')
DEBUG = config.getboolean('main', 'debug', fallback=False)
SERVE_BRANCHES = config.getboolean('main', 'serve_branches', fallback=False)


def compare_event_signature():
    receive_signature = request.environ['HTTP_X_HUB_SIGNATURE']
    secret = str.encode(EVENT_SECRET)
    payload = request.body.read()
    computed_sha1 = hmac.new(secret, payload, hashlib.sha1).hexdigest()
    return hmac.compare_digest(receive_signature, 'sha1=%s' % computed_sha1)


def sanitize(str):
    keepcharacters = ('.', '_')
    return "".join(c for c in str if c.isalnum() or c in keepcharacters)


def handle_push(json):
    log = get_logger()
    ref = json['ref'].rsplit('/', 1)[-1]  # refs/heads/branch
    sha = json['after']
    directory = sanitize(ref)
    git_url = json['repository']['ssh_url']
    log.info('Handling push for %s %s -> %s %s', git_url, ref, directory, sha)
    try:
        output = subprocess.check_output(['scripts/handle_push.sh', git_url, directory, sha], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = b'Error ' + e.output

    with open("branches/%s/%s.logs" % (directory, sha), "wb") as log_file:
        log_file.write(output)

    log.error(output)


@route('/events', method='POST')
def events():

    if not compare_event_signature():
        response.status = '403 Unauthorized'
        return {"error": "Bad event signature"}

    event = request.get_header('X-GitHub-Event')
    json = request.json
    repository = json['repository']['full_name']

    if repository != REPO:
        response.status = '403 Unauthorized'
        return {"error": "Unhandled repo %s" % repository}

    if event == 'ping':
        return {'response': 'pong'}
    elif event == 'push':
        p = Process(target=handle_push, args=(json,))
        p.daemon = True
        p.start()
        return {'status': 'Started handling push'}

    response.status = '500 Internal Error'
    return {"error": "Unhandled event %s" % event}


@route('/')
def main():
    branches = os.listdir('branches')
    print(branches)
    return "\n".join(branches)


script_dirname = os.path.dirname(os.path.realpath(__file__))
@route('/branches/<filepath:path>')
def server_static(filepath):
    if SERVE_BRANCHES:
        return static_file(filepath, root='%s/branches' % script_dirname)
    else:
        response.status = '403 Unauthorized'
        return {"error": "No statics configured"}


run(host='0.0.0.0', port=8080, debug=DEBUG)
