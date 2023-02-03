# -*- coding: utf-8 -*-
import os
import sys
import traceback
import webbrowser
from configparser import ConfigParser
from datetime import datetime

import requests
import rumps
import simplejson

VERSION = '0.5.0'
APP_NAME = 'Nightscout Menubar'
PROJECT_HOMEPAGE = 'https://github.com/kretep/nightscout-osx-menubar'

SGVS_PATH = '/api/v1/entries/sgv.json?count={count}'
DEVICESTATUS_PATH = '/api/v1/devicestatus/'
UPDATE_FREQUENCY_SECONDS = 20
MAX_SECONDS_TO_SHOW_DELTA = 600
HISTORY_LENGTH = 5
MAX_BAD_REQUEST_ATTEMPTS = 3
REQUEST_TIMEOUT_SECONDS = 2

################################################################################
# Display options        

MENUBAR_TEXT = "{devicestatus} {sgv}{direction} {delta} [{time_ago}]"
MENU_ITEM_TEXT = "{sgv}{direction} {delta} [{time_ago}]"

def time_ago(seconds):
    if seconds >= 3600:
        return "%sh" % round((seconds / 3600), 1)
    else:
        return "%sm" % int((seconds / 60))


################################################################################

class NightscoutException(Exception): pass

class NightscoutConfig(object):
    FILENAME = 'config'
    SECTION = 'NightscoutMenubar'
    HOST = 'nightscout_host'
    USE_MMOL = 'use_mmol'

    def __init__(self, app_name):
        self.config_path = os.path.join(rumps.application_support(app_name), self.FILENAME)
        self.config = ConfigParser()
        self.config.read([self.config_path])
        if not self.config.has_section(self.SECTION):
            self.config.add_section(self.SECTION)
        if not self.config.has_option(self.SECTION, self.HOST):
            self.set_host('')
        if not self.config.has_option(self.SECTION, self.USE_MMOL):
            self.set_use_mmol(False)

    def get_host(self):
        return self.config.get(self.SECTION, self.HOST)

    def set_host(self, host):
        self.config.set(self.SECTION, self.HOST, host)
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get_use_mmol(self):
        return bool(self.config.get(self.SECTION, self.USE_MMOL))

    def set_use_mmol(self, mmol):
        self.config.set(self.SECTION, self.USE_MMOL, 'true' if mmol else '')
        with open(self.config_path, 'w') as f:
            self.config.write(f)

config = NightscoutConfig(APP_NAME)

def maybe_convert_units(mgdl):
    return round(mgdl / 18.018, 1) if config.get_use_mmol() else mgdl

def update_menu(title, items):
    app.title = title
    app.menu.clear()
    app.menu.update(items + last_updated_menu_items() + post_history_menu_options() + [app.quit_button])

def last_updated_menu_items():
    return [
        None,
        "Updated %s" % datetime.now().strftime("%a %-I:%M %p"),
    ]

def post_history_menu_options():
    mgdl = rumps.MenuItem('mg/dL', callback=choose_units_mgdl)
    mgdl.state = not config.get_use_mmol()
    mmol = rumps.MenuItem('mmol/L', callback=choose_units_mmol)
    mmol.state = config.get_use_mmol()
    open_ns_url = rumps.MenuItem('Open Nightscout site...', callback=None)
    if config.get_host():
        open_ns_url.set_callback(open_nightscout_url)
    items = [
        None,
        [
            'Settings',
            [
                mgdl,
                mmol,
                None,
                rumps.MenuItem('Set Nightscout URL...', callback=configuration_window),
                rumps.MenuItem('Help...', callback=open_project_homepage),
                None,
                "Version {}".format(VERSION)
            ],
        ],
        None,
        open_ns_url,
        None,
    ]
    return items

def get_entries(retries=0, last_exception=None):
    if retries >= MAX_BAD_REQUEST_ATTEMPTS:
        print("Retried too many times: %s" % last_exception)
        raise NightscoutException(last_exception)

    try:
        resp = requests.get(
            config.get_host() + SGVS_PATH.format(count=(HISTORY_LENGTH + 1)),
            #TODO: https://github.com/psf/requests/issues/557#issuecomment-7149390
            # For the sake of keeping this portable without adding a lot of complexity, don't verify SSL certificates.
            # https://github.com/kennethreitz/requests/issues/557
            verify=False,
            # Don't let bad connectivity cause the app to freeze
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout as e:
        # Don't retry timeouts, since the app is unresponsive while a request is in progress,
        # and a new request will be made in UPDATE_FREQUENCY_SECONDS seconds anyway.
        print("Timed out: %s" % repr(e))
        raise NightscoutException(repr(e))
    except requests.exceptions.RequestException as e:
        return get_entries(retries + 1, repr(e))

    if resp.status_code != 200:
        return get_entries(retries + 1, "Nightscout returned status %s" % resp.status_code)

    try:
        arr = resp.json()
        if type(arr) == list and (len(arr) == 0 or type(arr[0]) == dict):
            return arr
        else:
            return get_entries(retries + 1, "Nightscout returned bad data")
    except simplejson.scanner.JSONDecodeError:
        return get_entries(retries + 1, "Nightscout returned bad JSON")

def get_devicestatus(retries=0, last_exception=None):
    if retries >= MAX_BAD_REQUEST_ATTEMPTS:
        print("Retried too many times: %s" % last_exception)
        raise NightscoutException(last_exception)

    try:
        resp = requests.get(
            config.get_host() + DEVICESTATUS_PATH,
            #TODO: https://github.com/psf/requests/issues/557#issuecomment-7149390
            # For the sake of keeping this portable without adding a lot of complexity, don't verify SSL certificates.
            # https://github.com/kennethreitz/requests/issues/557
            verify=False,
            # Don't let bad connectivity cause the app to freeze
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout as e:
        # Don't retry timeouts, since the app is unresponsive while a request is in progress,
        # and a new request will be made in UPDATE_FREQUENCY_SECONDS seconds anyway.
        print("Timed out: %s" % repr(e))
        raise NightscoutException(repr(e))
    except requests.exceptions.RequestException as e:
        return get_devicestatus(retries + 1, repr(e))

    if resp.status_code != 200:
        return get_devicestatus(retries + 1, "Nightscout returned status %s" % resp.status_code)

    try:
        arr = resp.json()
        if type(arr) == list and (len(arr) == 0 or type(arr[0]) == dict):
            return arr
        else:
            return get_devicestatus(retries + 1, "Nightscout returned bad data")
    except simplejson.scanner.JSONDecodeError:
        return get_devicestatus(retries + 1, "Nightscout returned bad JSON")        

def filter_bgs(entries):
    bgs = [e.copy() for e in entries if 'sgv' in e]
    for bg in bgs:
        bg['sgv'] = int(bg['sgv'])
    return bgs

def seconds_ago(timestamp):
    return int(datetime.now().strftime('%s')) - timestamp / 1000

def get_direction(entry):
    return {
        'DoubleUp': '⇈',
        'SingleUp': '↑',
        'FortyFiveUp': '↗',
        'Flat': '→',
        'FortyFiveDown': '↘',
        'SingleDown': '↓',
        'DoubleDown': '⇊',
    }.get(entry.get('direction'), '-')

def get_delta(last, second_to_last):
    return ('+' if last['sgv'] >= second_to_last['sgv'] else '−') + str(abs(maybe_convert_units(last['sgv'] - second_to_last['sgv'])))

def get_menubar_text(entries, devicestatus):
    bgs = filter_bgs(entries)
    last, second_to_last = bgs[0:2]
    if (last['date'] - second_to_last['date']) / 1000 <= MAX_SECONDS_TO_SHOW_DELTA:
        delta = get_delta(last, second_to_last)
    else:
        delta = '?'
    #TODO: status doesn't contain mills?
    #last_loop = devicestatus[0]['mills']
    loop_delta = 60 #TODO: fix
    loop_status = '⚠'
    if loop_delta < 300:
        loop_status = '↻'
    if loop_delta > 1200:
        loop_status = '⚡'
    return MENUBAR_TEXT.format(
        sgv=maybe_convert_units(last['sgv']),
        delta=delta,
        direction=get_direction(last),
        time_ago=time_ago(seconds_ago(last['date'])),
        devicestatus=loop_status,
    )

def get_history_menu_items(entries):
    bgs = filter_bgs(entries)
    return [
        MENU_ITEM_TEXT.format(
            sgv=maybe_convert_units(e['sgv']),
            delta=get_delta(e, bgs[i + 1]) if i + 1 < len(bgs) else '?',
            direction=get_direction(e),
            time_ago=time_ago(seconds_ago(e['date'])),
        )
        for i, e in enumerate(bgs)
    ][1:HISTORY_LENGTH + 1]

@rumps.timer(UPDATE_FREQUENCY_SECONDS)
def update_data(sender):
    entries = None
    try:
        try:
            entries = get_entries()
            devicestatus = get_devicestatus()
        except NightscoutException as e:
            if config.get_host():
                update_menu("<?>", [e.message[:100]])
            else:
                update_menu("<Need settings>", [])
        else:
            update_menu(get_menubar_text(entries, devicestatus), get_history_menu_items(entries))
    except Exception as e:
        print("Nightscout data: " + simplejson.dumps(entries))
        print(repr(e))
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)
        update_menu("<!>", [repr(e)[:100]])

def configuration_window(sender):
    window = rumps.Window(
        title='Nightscout Menubar Configuration',
        message='Enter your nightscout URL below.\n\nIt probably looks like:\nhttps://SOMETHING.herokuapp.com',
        dimensions=(320, 22),
    )
    window.default_text = config.get_host()
    window.add_buttons('Cancel')

    response = window.run()
    if response.clicked == 1:
        config.set_host(response.text.strip())
        update_data(None)

def open_project_homepage(sender):
    webbrowser.open_new(PROJECT_HOMEPAGE)

def open_nightscout_url(sender):
    webbrowser.open_new(config.get_host())

def choose_units_mgdl(sender):
    config.set_use_mmol(False)
    update_data(None)

def choose_units_mmol(sender):
    config.set_use_mmol(True)
    update_data(None)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        rumps.debug_mode(True)
    app = rumps.App(APP_NAME, title='<Connecting to Nightscout...>')
    app.menu = ['connecting...'] + post_history_menu_options()
    app.run()
