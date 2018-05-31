import json
import os
import subprocess
import subprocess2
import sys
import time
import traceback
import urllib2

import detect_host_arch
import gclient_utils
import scm


DEPOT_TOOLS = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(DEPOT_TOOLS, 'monitoring.cfg')

CHILD_PID = 0
DEFAULT_COUNTDOWN = 10
APP_URL = 'https://lemur-swarming.appspot.com'

DISABLE_MONITORING = False


def _get_monitoring_config():
  """Read the monitoring config from CONFIG_FILE or return a default one."""
  try:
    with open(CONFIG_FILE) as f:
      config = json.load(f)
  except (IOError, ValueError):
    # If we couldn't load the config file, return a new config object.
    # 'is-google' is the only field that needs special initialization, since the
    # other variables have simple default values.
    req = urllib2.urlopen(APP_URL + '/should-upload')
    # /should-upload is only accessible from Google IPs, so we only need to
    # check if we can reach the page. An external developer would get an access
    # denied code.
    config = {'is-googler': req.getcode() == 200}

  # Make sure the config variables we need are present, and initialize them to
  # safe values otherwise.
  config.setdefault('is-googler', False)
  config.setdefault('countdown', DEFAULT_COUNTDOWN)
  config.setdefault('opt-in', None)

  return config

C = _get_monitoring_config()


def _get_python_version():
  """Return the python version in the major.minor.micro format."""
  return '{v.major}.{v.minor}.{v.micro}'.format(v=sys.version_info)

def _return_code_from_exception(exception):
  """Returns the exit code that would result of raising the exception."""
  if exception is None:
    return 0
  if isinstance(exception[1], SystemExit):
    return exception[1].code
  return 1

def _seconds_to_weeks(duration):
  """Transform a |duration| from seconds to weeks approximately.

  Drops the lowest 19 bits of the integer representation, which ammounts to
  about 6 days.
  """
  return int(duration) >> 19

def _get_repo_timestamp(path_to_repo):
  """Get an approximate timestamp for the upstream of |path_to_repo|.

  Returns the top two bits of the timestamp of the HEAD for the upstream of the
  branch path_to_repo is checked out at.
  """
  # Get the upstream for the current branch. If we're not in a branch, then give
  # up.
  try:
    upstream = scm.GIT.GetUpstreamBranch(path_to_repo)
  except subprocess2.CalledProcessError:
    return None

  # Get the timestamp of the HEAD for the upstream of the current branch.
  p = subprocess.Popen(
      ['git', '-C', path_to_repo, 'log', '-n1', upstream, '--format=%at'],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, _ = p.communicate()

  # If there was an error, give up.
  if p.returncode != 0:
    return None

  # Get the age of the checkout in weeks.
  return _seconds_to_weeks(stdout.strip())

def _upload_monitoring_data(exception, execution_time):
  """Upload the monitoring data to the AppEngine app."""
  data = _REPORTED_DATA
  data.update({
      'timestamp': _seconds_to_weeks(time.time()),
      'python_version': _get_python_version(),
      'host_os': gclient_utils.GetMacWinOrLinux(),
      'host_arch': detect_host_arch.HostArch(),
      'depot_tools_age': _get_repo_timestamp(DEPOT_TOOLS),
      'return_code': _return_code_from_exception(exception),
      'execution_time': execution_time,
  })

  urllib2.urlopen(APP_URL + '/upload', json.dumps(data))

def _print_notice():
  """Print a notice to let the user know the status of monitoring."""
  # TODO(ehmaldonado): Make the colors and ASCII boxes. Reference a
  # monitoring.README file that explains what we are collecting and how to
  # opt-in/out.
  if C['countdown'] == 0:
    print "MONITORING IS TAKING PLACE"
  else:
    print "MONITORING WILL TAKE PLACE IN %d EXECUTIONS" % C['countdown']
    # Update the countdown.
    C['countdown'] -= 1
    with open(CONFIG_FILE, 'w') as f:
      json.dump(C, f)


def monitoring_wrapper(func):
  """Wraps a function execution and uploads monitoring data after completion.
  """
  def _inner(*args, **kwargs):
    exception = None
    try:
      start = time.time()
      func(*args, **kwargs)
    # pylint: disable=bare-except
    except:
      exception = sys.exc_info()
    finally:
      execution_time = time.time() - start

    # Print the exception before the monitoring notice, so that the notice is
    # clearly visible even if gclient fails.
    if exception and not isinstance(exception[1], SystemExit):
      traceback.print_exception(*exception)

    # Print the monitoring notice only if the user has not explicitly opted in
    # or out.
    if C['opt-in'] is None:
      _print_notice()

    if os.fork() == CHILD_PID:
      # Catch all exceptions, so we don't interrupt the user workflow.
      try:
        _upload_monitoring_data(exception, execution_time)
      # pylint: disable=bare-except
      except:
        pass
    else:
      sys.exit(_return_code_from_exception(exception))

  # If the user has opted out or the user is not a googler, then there is no
  # need to do anything.
  if C['opt-in'] == False or not C['is-googler']:
    return func
  # If DEPOT_TOOLS_MONITORING = 0 in the environment variables, disable
  # monitoring as well.
  if os.environ.get('DEPOT_TOOLS_MONITORING') == '0':
    return func
  return _inner


_REPORTED_DATA = {}

def report(name, value):
  """Report a value with the given name."""
  # TODO(ehmaldonado): Make this into an object and put some locks?
  _REPORTED_DATA[name] = value
