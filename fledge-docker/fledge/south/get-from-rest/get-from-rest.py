# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

""" 
South plugin for Fledge to GET data from REST API.
Built for Masters Thesis project in 2024 by Markus Oja
For Fledge v2.4.0
"""

import copy
import asyncio
import json
import logging
from threading import Thread
import aiohttp
from datetime import datetime, timezone

from fledge.common import logger
import async_ingest

_LOGGER = logger.setup(__name__, level=logging.DEBUG)

PLUGIN_NAME = 'get-from-rest'

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'GET data from REST APIs',
        'type': 'string',
        'default': PLUGIN_NAME,
        'readonly': 'true'
    },

    'assetName': {
        'description': 'Name of Asset',
        'type': 'string',
        'default': 'simple',
        'displayName': 'Asset name',
        'mandatory': 'true'
    },

    'url': {
        'description': 'URL to GET from',
        'type': 'string',
        'default': 'place-url-here',
        'displayName': 'URL',
        'mandatory': 'true'
    },

    'headers': {
        'description': 'Headers as JSON',
        'type': 'JSON',
        'default': json.dumps({'x-api-key': 'api-key-here'}),
        'displayName': 'Headers',
        'mandatory': 'false'
    },

    'wrapper': {
        'description': 'JSON defining key name and location in data',
        'type': 'JSON',
        'default': json.dumps({
            'datasetId': 'datasetId',
            'time': 'startTime',
            'value': 'value'
            }),
        'displayName': 'Wrapper',
        'mandatory': 'false'
    },

    'interval': {
        'description': 'Time waiting between calls in seconds',
        'type': 'integer',
        'default': '10',
        'displayName': 'Interval between calls in secs',
        'mandatory': 'false'
    }
}


def plugin_info():

    """Used only once when call will be made to a plugin.

    Return information about the plugin including the configuration for the
    plugin. This is the same as plugin_info in all other types of plugin and
    is part of the standard plugin interface.

    Args:

    Returns:
        handle: Information about the plugin including the configuration for 
                the plugin
    """
    
    info = {
        'name': PLUGIN_NAME,
        'version': '2.4.0',
        'mode': 'async',
        'type': 'south',
        'interface': '2.0',
        'config': _DEFAULT_CONFIG
    }

    return info

def plugin_init(config):
    
    """
    Part of the standard plugin interface. 
    This call is passed the request configuration of the plugin and should be
    used to do any initialization of the plugin.
    """

    handle = copy.deepcopy(config)

    handle['plugin'] = SouthPlugin(handle)
    _LOGGER.debug('Plugin initialized')

    return handle


def plugin_start(handle):

    plugin = handle['plugin']

    plugin.loop = asyncio.new_event_loop()

    try:
        plugin.start()

        def run():
            plugin.loop.run_forever()

        plugin.thread = Thread(target=run)
        plugin.thread.start()
    except Exception as err:
        _LOGGER.exception(f'{PLUGIN_NAME} plugin failed to start. Details {str(err)}')
        raise


def plugin_reconfigure(handle, new_config):

    old_plugin = handle['plugin']

    old_callback = old_plugin.callback
    old_ingest_ref = old_plugin.ingest_ref

    plugin_shutdown(handle)

    new_handle = plugin_init(new_config)

    new_plugin = new_handle['plugin']
    new_plugin.callback = old_callback
    new_plugin.ingest_ref = old_ingest_ref

    
    plugin_start(new_handle)
    
    return new_handle


def plugin_shutdown(handle):

    try:
        _LOGGER.info(f'South plugin {PLUGIN_NAME} is shutting down.')
        plugin = handle['plugin']
        plugin.stop()
        plugin.loop.stop()
    except Exception as e:
        _LOGGER.exception(str(e))
        raise
    _LOGGER.info('South plugin {PLUGIN_NAME} shut down.')


def plugin_register_ingest(handle, callback, ingest_ref):
    """Required plugin interface component to communicate to South C server

    Args:
        handle: handle returned by the plugin initialisation call
        callback: C opaque object required to passed back to C->ingest method
        ingest_ref: C opaque object required to passed back to C->ingest method
    """
    _LOGGER.debug("Plugin register ingest...")

    plugin = handle['plugin']

    plugin.callback = callback
    plugin.ingest_ref = ingest_ref


class SouthPlugin(object):
    """ 
    Actual code to communicate with source
    Using threading and loop
    """

    def __init__(self, handle):
        self.url = handle['url']['value']
        self.headers = handle['headers']['value']
        self.asset = handle['assetName']['value']
        self.wrapper = handle['wrapper']['value']
        
        self.ingest_ref = None
        self.callback = None

        self.loop = None
        self.thread  = None

        self._interval = int(handle['interval']['value'])
        self._handler = None

        # parse wrapper
        wrapper =  {}
        try:
            for reading_name, json_location in self.wrapper.items():
                wrapper[reading_name] = json_location
        # need to catch some json errors...
        except Exception:
            pass
        self.parsed_wrapper = wrapper

    def _run(self):
        """ Run looper every (interval) seconds"""
        self.looper()
        self._handler = self.loop.call_later(self._interval, self._run)

    def start(self):
        self._handler = self.loop.call_later(self._interval, self._run)

    def stop(self):
        self._handler.cancel()

    def looper(self):
        """
        Actual code to run in loops
        """
        self.loop.create_task(self.fetch())

    async def fetch(self):
        _LOGGER.debug("Plugin polling...")
        data = None
        raw_data = None
        status = None

        try:
            raw_data, status = await self.get_data()
            if (status == 200):
                data = self.format_data(raw_data)
                _LOGGER.debug('Got data...')
            else:
                _LOGGER.info(f'Wrong status: {status}')

        except KeyError as exc:
            _LOGGER.error(f'Key mismatch: {exc}')
        except Exception as exc:
            _LOGGER.error(f'Data fetching error: {exc}')

        else:
            _LOGGER.debug("Returning data...")
            async_ingest.ingest_callback(self.callback, self.ingest_ref, data)
        
    async def get_data(self):
        """
        Request the data from url using headers

        Args:

        Return:
            resp: response json formatted
            status: status code
        """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=self.headers) as response:
                    status = response.status
                    resp = await response.json()
            
        except (Exception, RuntimeError) as err:
            _LOGGER.error(f'Error with session: {err}')
            raise err

        return resp, status

    def format_data(self, raw_data):
        """
        Pass the values forward...
        
        Args:
            raw_data:
        Returns:
            data: a dict with:
                asset: The asset key of the sensor device that is being read
                timestamp: A timestamp for the reading data
                readings: The reading data itself as a JSON object

        """
        readings = {}
        for key, value in self.parsed_wrapper.items():
            readings[key] = raw_data[value]

        # note: this timestamp is now, not when the reading itself was recorded
        time_stamp = str(datetime.now(tz=timezone.utc))

        data = {
            'asset': self.asset,
            'timestamp': time_stamp,
            'readings': readings
        }

        return data
