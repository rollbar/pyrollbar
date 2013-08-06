import optparse
import sys

import rollbar

VERSION = '0.1'

verbose = False

def _gen_report_message(level):
    def _wrapped(lines):
        line_data = '\n'.join(lines)
        if verbose:
            print 'Rollbar [%s]: %s' % (level, line_data)
        rollbar.report_message(line_data, level=level, extra_data={'cli_version': VERSION})
    return _wrapped


CMDS = {
    'debug': _gen_report_message('debug'),
    'info': _gen_report_message('info'),
    'warning': _gen_report_message('warning'),
    'error': _gen_report_message('error'),
    'critical': _gen_report_message('critical'),
}

def main():
    global verbose
    parser = optparse.OptionParser(version='%prog version ' + VERSION)
    parser.add_option('-t', '--access_token',
                      dest='access_token',
                      help="You project's access token from rollbar.com.",
                      metavar='ACCESS_TOKEN')
    parser.add_option('-e', '--environment',
                      dest='environment',
                      help="The environment to report errors and messages to.",
                      metavar='ENVIRONMENT')
    parser.add_option('-u', '--url',
                      dest='endpoint_url',
                      help="The Rollbar API endpoint url to send data to.",
                      metavar='ENDPOINT_URL',
                      default=rollbar.DEFAULT_ENDPOINT)
    parser.add_option('-v', '--verbose',
                      dest='verbose',
                      help="Print verbose output.",
                      action='store_true',
                      default=False)

    options, args = parser.parse_args()

    access_token = options.access_token
    env = options.environment
    endpoint = options.endpoint_url
    verbose = options.verbose

    if not access_token:
        parser.error('missing access_token')
    if not env:
        parser.error('missing environment')

    rollbar.init(access_token, environment=env, endpoint=endpoint)

    def _do_cmd(cmd_name, lines):
        cmd = CMDS.get(cmd_name.lower())
        if cmd:
            cmd(lines)
            return True

        return False

    if len(args) > 1:
        sent = _do_cmd(args[0], [' '.join(args[1:])])
        sys.exit(0 if sent else 1)

    cur_cmd_name = None
    lines = []
    cur_line = sys.stdin.readline()
    while cur_line:
        cur_line = cur_line.strip()
        parts = cur_line.split(' ')

        if cur_cmd_name is None:
            cur_cmd_name = parts[0] if parts else None
            parts = parts[1:]

        if not cur_line and cur_cmd_name:
            if _do_cmd(cur_cmd_name, lines):
                lines = []
                cur_cmd_name = None
        else:
            lines.append(' '.join(parts))

        cur_line = sys.stdin.readline()

    if cur_cmd_name and lines:
        _do_cmd(cur_cmd_name, lines)
