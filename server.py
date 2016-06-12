import bottle
from bottle import request, response, route, static_file, template
from multiprocessing import Process, get_logger as get_logger_internal

from ansi2html import Ansi2HTMLConverter

import hashlib
import hmac
import os
import fcntl
import time
import json as JSON
import logging

import sys
PY3 = sys.version_info[0] == 3

if PY3:
    import configparser
    import subprocess
    from time import monotonic
else:
    import subprocess32 as subprocess
    from monotonic import monotonic
    from backports import configparser

SCRIPT_DIRNAME = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
config.read('config.ini')
REPO = config.get('main', 'allowed')
EVENT_SECRET = config.get('main', 'event_secret')
DEBUG = config.getboolean('main', 'debug', fallback=False)
SERVE_BRANCHES = config.getboolean('main', 'serve_branches', fallback=False)
HANDLE_PUSH_TIMEOUT = config.getint('main', 'handle_push_timeout', fallback=600)
DISABLE_BOTTLE_ERROR_HANDLING = config.getboolean('main', 'disable_bottle_error_handling', fallback=False)


logger = None
def get_logger():
    global logger
    if logger is None:
        logger = get_logger_internal()
        hdlr = logging.FileHandler('binocular_logs.txt')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    return logger


def compare_event_signature():
    receive_signature = request.environ['HTTP_X_HUB_SIGNATURE']
    secret = str.encode(EVENT_SECRET) if PY3 else str(EVENT_SECRET)
    payload = request.body.read()
    computed_sha1 = hmac.new(secret, payload, hashlib.sha1).hexdigest()
    return hmac.compare_digest(receive_signature, 'sha1=%s' % computed_sha1)


def sanitize(str):
    keepcharacters = ('.', '_')
    return "".join(c for c in str if c.isalnum() or c in keepcharacters)


def write_status(branch, sha, status):
    get_logger().debug('writing status %s %s %s', branch, sha, status)
    assert status in ['failed', 'pending', 'success']
    status_filename = "branches/%s/%s.status" % (branch, sha)
    with open(status_filename, "w") as status_file:
        status_file.write(status)


def read_status(branch, sha):
    status_filename = "branches/%s/%s.status" % (branch, sha)
    with open(status_filename, "r") as status_file:
        status = status_file.read()
    assert status in ['failed', 'pending', 'success']
    return status


conv = Ansi2HTMLConverter(escaped=False)
def read_continuously(filename, delay=0.5, timeout=120, to_html=False):
    try:
        with open(filename, 'r') as f:
            fd = f.fileno()
            flag = fcntl.fcntl(fd, fcntl.F_GETFD)
            fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            previous_tick = monotonic()
            while True:
                current_tick = monotonic()
                if current_tick - previous_tick > timeout:  # in seconds
                    return

                new = f.readline()
                if new:
                    previous_tick = current_tick
                    if to_html:
                        html = conv.convert(new, full=False)
                        yield(html)
                    else:
                        yield(new)
                else:
                    time.sleep(delay)  # in seconds
    except:
        get_logger().exception('Error reading %s', filename)
        raise


def handle_push(json):
    log = get_logger()
    ref = json['ref'].rsplit('/', 1)[-1]  # refs/heads/branch
    sha = json['after']
    directory = sanitize(ref)
    git_url = json['repository']['ssh_url']
    log.info('Handling push for %s %s -> %s %s', git_url, ref, directory, sha)

    if not os.path.exists('branches/' + directory):
        os.makedirs('branches/' + directory)
    filename = 'branches/%s/%s_event.log' % (directory, sha)
    with open(filename, 'w') as event_file:
        event = JSON.dumps(json, sort_keys=True, indent=4, separators=(',', ': '))
        event_file.write(event)

    write_status(directory, sha, 'pending')

    filename = 'branches/%s/%s_build.log' % (directory, sha)
    open(filename, 'a').close()  # create file
    with open(filename, 'wb') as log_file:
        try:
            return_code = subprocess.call(
                ['scripts/handle_push.sh', git_url, directory, sha],
                stdout=log_file, stderr=subprocess.STDOUT,
                timeout=HANDLE_PUSH_TIMEOUT)
            if return_code == 0:
                write_status(directory, sha, 'success')
                return
        except:
            log.exception('Error in handle_push')
    write_status(directory, sha, 'failed')


@route('/events', method='POST')
def events():
    log = get_logger()

    if not compare_event_signature():
        log.warning('Recevied an event with a bad signature')
        response.status = '403 Unauthorized'
        return {"error": "Bad event signature"}

    event = request.get_header('X-GitHub-Event')
    json = request.json
    repository = json['repository']['full_name']

    log.debug('Received an event %s', event)
    if repository != REPO:
        response.status = '403 Unauthorized'
        return {"error": "Unhandled repo %s" % repository}

    if event == 'ping':
        log.info('Success: got a ping from github!')
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
            'status': read_status(dir_branch, s),
            'name': s,
            'date': os.path.getmtime('branches/%s/%s' % (dir_branch, s))
        } for s in dir_shas]

        branches.append({'name': dir_branch, 'shas': shas})
    return template("config/templates/list_branches_and_sha", branches=branches)


@route('/branches/<branch>/<sha>_build.log')
def stream(branch, sha):
    osfilepath = '%s/branches/%s/%s_build.log' % (SCRIPT_DIRNAME, branch, sha)
    if not os.path.isfile(osfilepath):
        response.status = '404 Not Found'
        return response

    main_generator = read_continuously(osfilepath, to_html=True, timeout=122)

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


@route('/branches/<branch>/<sha>/<filepath:path>')
def serve_branches(branch, sha, filepath):
    if SERVE_BRANCHES:
        return static_file(filepath, root='%s/branches/%s/%s' % (SCRIPT_DIRNAME, branch, sha))
    else:
        response.status = '403 Unauthorized'
        return {"error": "No statics configured"}


@route('/status/<branch>/<sha>')
def status(branch, sha):
    return template("config/templates/status.tpl", branch=branch, sha=sha)


if DISABLE_BOTTLE_ERROR_HANDLING:
    bottle.default_app().catchall = False

bottle.run(host='0.0.0.0', port=8080, debug=DEBUG)
