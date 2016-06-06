import subprocess
from bottle import run, request, response, route, static_file, template
from multiprocessing import Process, get_logger

from ansi2html import Ansi2HTMLConverter

import hashlib
import hmac
import os
import fcntl
import time
import configparser
import html


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
    dir_branches = next(os.walk('branches'))[1]
    branches = []
    for dir_branch in dir_branches:
        dir_shas = next(os.walk('branches/%s' % dir_branch))[1]
        shas = [{
            'name': s,
            'date': os.path.getmtime('branches/%s/%s' % (dir_branch, s))
        } for s in dir_shas]

        branches.append({'name': dir_branch, 'shas': shas})
    return template("templates/list_branches_and_sha", branches=branches)


conv = Ansi2HTMLConverter()
def read_continuously(filename, delay=0.5, timeout=120, to_html=False, sanitize=False):
    with open(filename, 'r') as f:
        fd = f.fileno()
        flag = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
        previous_tick = time.monotonic()
        while True:
            current_tick = time.monotonic()
            if current_tick - previous_tick > timeout:  # in seconds
                return

            new = f.readline()
            if new:
                previous_tick = current_tick
                if to_html:
                    if sanitize:
                        new = html.escape(new)
                    yield(conv.convert(new, full=False))
                else:
                    yield(new)
            else:
                time.sleep(delay)  # in seconds


@route('/logs/<filename>')
def stream(filename):
    osfilepath = '%s/logs/%s' % (SCRIPT_DIRNAME, filename)
    if not os.path.isfile(osfilepath):
        response.status = '404 Not Found'
        return response

    main_generator = read_continuously(osfilepath, to_html=True, sanitize=False, timeout=122)

    def full_generator():
            yield('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
            yield('<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
            yield(conv.produce_headers())
            yield('<body class="body_foreground body_background" style="font-size: normal;" ><pre class="ansi2html-content">')
            for line in main_generator:
                yield(line)
            yield('</pre> </body> </html>')

    if request.query.get('embed') is None:
        return full_generator()
    else:
        return main_generator


@route('/static/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root='%s/static' % SCRIPT_DIRNAME)


@route('/branches/<filepath:path>')
def serve_branches(filepath):
    if SERVE_BRANCHES:
        return static_file(filepath, root='%s/branches' % SCRIPT_DIRNAME)
    else:
        response.status = '403 Unauthorized'
        return {"error": "No statics configured"}


@route('/status/<branch>/<sha>')
def status(branch, sha):
    return template("templates/status.tpl", branch=branch, sha=sha)


run(host='0.0.0.0', server="paste", port=8080, debug=DEBUG)
