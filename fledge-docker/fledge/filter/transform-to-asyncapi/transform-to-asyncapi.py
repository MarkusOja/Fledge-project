# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

"""
Filter plugin for Fledge to transform data to AsyncAPI format
Built for Masters Thesis project in 2024 by Markus Oja
For Fledge v2.4.0
"""

import logging
from copy import deepcopy
import json

from fledge.common import logger
import filter_ingest

_LOGGER = logger.setup(__name__, level=logging.DEBUG)

PLUGIN_NAME = "transform-to-asyncapi"


JSON_DYNAMIC = {
    "data": {
        "IdentifiedObject.mRID": {
            "CONFIG": 
                {"LOCATION": "locationInReadings"}
                },
        "MeasurementValueSource.source.name": "Fledge"
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
        "description": "payload example in json",
        "type": "JSON",
        "default": json.dumps(JSON_DYNAMIC),
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
    _LOGGER.info(f'Old config {handle} \n new config {new_config} for {PLUGIN_NAME} plugin')
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
        # need to keep the stuff same to not mess with the North plugin
        # modify only the readings-part
        readings = element.get('readings')
        
        if readings:
            # go through the json and replace keywords with reading values
            new_data = replace_pointers(handle['json']['value'], readings)
            _LOGGER.debug(f'filtered element {element}')
            element['readings'] = new_data
        # add the modified readings to list
        processed_data.append(element)

    _LOGGER.debug(f'Readings after: {processed_data}')

    # Pass data onwards
    filter_ingest.filter_ingest_callback(
        handle["callback"],  
        handle["ingestRef"], 
        processed_data
        )

    _LOGGER.debug(f'{PLUGIN_NAME} filter ingest done')


def replace_pointers(config, readings):
    def replace_keywords(copy_of_config_json):
        """
        TODO: use vars instead of hard coded...
        add format thing...
        """
        # try using list to not run into error
        for key, value in list(copy_of_config_json.items()):

            # if key = "CONFIG", replace that with the "LOCATION" (and "FORMAT")
            if isinstance(value, dict):
                if value.get("CONFIG"):

                    # use location to fill the value from readings
                    # TODO: cannot read values from nested keys
                    location = value['CONFIG'].get('LOCATION')
                    _LOGGER.debug(f'Replacing CONFIG with {location}')

                    new_value = readings.get(location)
                    if new_value:
                        copy_of_config_json[key] = new_value
                    else:
                        copy_of_config_json[key] = "NO VALUE"
                    _LOGGER.debug(f'It is now: {copy_of_config_json[key]}')

                else: # dig deeper
                    replace_keywords(value)
        return copy_of_config_json

    data = deepcopy(config)
    modified_data = replace_keywords(data)

    return modified_data

