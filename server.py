import subprocess
from bottle import run, request, response, route, static_file
from multiprocessing import Process, get_logger

from ansi2html import Ansi2HTMLConverter

import hashlib
import hmac
import os
import fcntl
import time
import configparser


SCRIPT_DIRNAME = os.path.dirname(os.path.realpath(__file__))

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

    filename = "logs/%s.log" % sha
    open(filename, 'a').close()  # create file
    with open(filename, "wb") as log_file:
        try:
            subprocess.Popen(['scripts/handle_push.sh', git_url, directory, sha], stdout=log_file, stderr=subprocess.STDOUT)
        except:
            log.exception('Error in handle_push')


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


conv = Ansi2HTMLConverter()
def read_continuously(filename, delay=0.5, timeout=120, to_html=False):
    with open(filename, 'r') as f:
        fd = f.fileno()
        flag = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
        previous_tick = time.monotonic()
        if to_html:
            yield('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
            yield('<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
            yield(conv.produce_headers())
            yield('<body class="body_foreground body_background" style="font-size: normal;" ><pre class="ansi2html-content">')
            yield('')
        while True:
            current_tick = time.monotonic()
            if current_tick - previous_tick > timeout:  # in seconds
                return
            new = f.readline()
            if new:
                if to_html:
                    yield(conv.convert(new, full=False))
                else:
                    yield(new)
            else:
                time.sleep(delay)  # in seconds
        if to_html:
            yield('</pre> </body> </html>')


@route('/logs/<filename>')
def stream(filename):
    osfilepath = '%s/logs/%s' % (SCRIPT_DIRNAME, filename)
    if not os.path.isfile(osfilepath):
        response.status = '404 Not Found'
        return response

    return read_continuously(osfilepath, to_html=True)


@route('/branches/<filepath:path>')
def server_static(filepath):
    if SERVE_BRANCHES:
        return static_file(filepath, root='%s/branches' % SCRIPT_DIRNAME)
    else:
        response.status = '403 Unauthorized'
        return {"error": "No statics configured"}


run(host='0.0.0.0', port=8080, debug=DEBUG)
