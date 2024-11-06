# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

"""
Filter plugin for Fledge to add UUID to data
Built for Masters Thesis project in 2024 by Markus Oja
For Fledge v2.4.0
"""

import logging
from copy import deepcopy
import json
import uuid

from fledge.common import logger
import filter_ingest

_LOGGER = logger.setup(__name__, level=logging.DEBUG)

PLUGIN_NAME = "add-uuid"

UUID_CONFIG = {
    "key1": "uuid",
    "key2": {
        "key": "uuid"
    }
}


_DEFAULT_CONFIG = {
    "plugin": {
        "description": "Filter to modify data...",
        "type": "string",
        "default": PLUGIN_NAME,
        "readonly": "true"
    },
    "json": {
        "description": "uuids to input",
        "type": "JSON",
        "default": json.dumps(UUID_CONFIG),
        "displayName": "Config json",
        "order": "1"
    },
    "enable": {
        "description": "Enable/Disable filter plugin",
        "type": "boolean",
        "default": "false",
        "displayName": "Enabled",
        "order": "2"
    }
}


def plugin_info():
    """Used only once when call will be made to a plugin.

    Return information about the plugin including the configuration for the
    plugin. This is the same as plugin_info in all other types of plugin and
    is part of the standard plugin interface.

    Args:

    Returns:
        Information about the plugin including the configuration for the plugin

    """

    info = {
        "name": PLUGIN_NAME,
        "version": "2.4.0",
        "mode": "none",
        "type": "filter",
        "interface": "2.0",
        "config": _DEFAULT_CONFIG
    }

    return info


def plugin_init(config, ingest_ref, callback):
    """ Initialise the plugin
    Args:
        config:     JSON configuration document for the Filter plugin configuration category
        ingest_ref: filter ingest reference
        callback:   filter callback
    Returns:
        handle:       JSON object to be used in future calls to the plugin
    Raises:
    """
    handle = deepcopy(config)
    handle["callback"] = callback
    handle["ingestRef"] = ingest_ref
    return handle


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    Args:
        handle:     handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    """
    _LOGGER.info(f'Old config {handle} \n new config {new_config} for {PLUGIN_NAME} plugin.')
    new_handle = deepcopy(new_config)
    new_handle["callback"] = handle["callback"]
    new_handle["ingestRef"] = handle["ingestRef"]
    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    """
    handle["callback"] = None
    handle["ingestRef"] = None
    _LOGGER.info(f'{PLUGIN_NAME} filter plugin shutdown.')


def plugin_ingest(handle, data):
    """ Modify readings data and pass it onward

    Args:
        handle: handle returned by the plugin initialisation call
        data:   readings data
    """
    if handle["enable"]["value"] == "false":
        # Filter not enabled, just pass data onwards
        filter_ingest.filter_ingest_callback(handle["callback"],  handle["ingestRef"], data)
        return

    # Filter is enabled: Get keys from json, get values for it from data
    processed_data = []

    _LOGGER.debug(f'Readings before: {data}')

    for element in data:
        # modify only the readings-part
        readings = element.get('readings')

        if readings:
            # go through the json and replace keywords generated values
            add_uuid(handle['json']['value'], readings)
            _LOGGER.debug(element)

        processed_data.append(element)

 
    _LOGGER.debug(f'Readings after: {processed_data}')

    # Pass data onwards
    filter_ingest.filter_ingest_callback(
        handle["callback"],  
        handle["ingestRef"], 
        processed_data
        )

    _LOGGER.debug(f'{PLUGIN_NAME} filter ingest done')


def add_uuid(config, readings):
    def find_and_generate(dictionary):
        """
        TODO: use vars instead of hard coded...
        add formatting...
        """
        # using list to prevent errors
        for key, value in list(dictionary.items()):

            # everything with a value should be right row
            if isinstance(value, dict):
                # go deeper
                find_and_generate(value)
            else:
                new_value = uuid.uuid4()
                # without str shows UUID('new_value')
                dictionary.update({key: str(new_value)})
        return dictionary
    
    # use deepcopy and update instead of modifying directly the readings
    data = deepcopy(config)
    modified_data = find_and_generate(data)

    # don't return, instead modify exising dictionary
    readings.update(modified_data)

