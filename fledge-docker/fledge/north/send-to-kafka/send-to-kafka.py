# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

"""
North plugin for Fledge to produce Kafka.
Built for Masters Thesis project in 2024 by Markus Oja
For Fledge v2.4.0
"""



import asyncio
import json

from copy import deepcopy

from kafka import KafkaProducer
from fledge.common import logger

_LOGGER = logger.setup(__name__)

PLUGIN_NAME = 'send-to-kafka'

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'AsyncAPI Kafka Plugin',
        'type': 'string',
        'default': PLUGIN_NAME,
        'readonly': 'true'
    },

    'topic': {
        'description': 'Topic of Kafka server',
        'type' : 'string',
        'default': 'Fledge',
        'order': '1'
    },

    ### Check the links for configurations:
    # https://kafka-python.readthedocs.io/en/master/_modules/kafka/producer/kafka.html#KafkaProducer
    # https://kafka.apache.org/0100/configuration.html#producerconfigs

    'configuration': {
        'description': 'Configuration JSON for KafkaProducer',
        'type': 'JSON',
        'default': json.dumps({
            "bootstrap_servers": "7e189678dcaf:9092"
        }),
        'order': '2',
        'displayName': 'Kafka configuration'
    },

    # source is needed for north plugin
    'source': {
         'description': 'Source of data to be sent North.',
         'type': 'enumeration',
         'default': 'readings',
         'options': ['readings', 'statistics'],
         'order': '3',
         'displayName': 'Source'
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
        'name': PLUGIN_NAME,
        'version': '2.4.0',
        'type': 'north',
        'interface': '2.0',
        'config': _DEFAULT_CONFIG
    }

    return info


def plugin_init(data):
    """Used for initialization of a plugin.

    Part of the standard plugin interface. This call is passed the
    request configuration of the plugin and should be used to do any
    initialization of the plugin.

    Args:
        data: plugin configuration
    Returns:
        handle: dictionary of a Plugin configuration

    """
    handle = deepcopy(data)

    # pass the json to the KafkaProducer
    config = handle['configuration']['value']
    handle['plugin'] = KafkaPlugin(**config)
 
    _LOGGER.debug(f'Init, handle: {handle}')

    return handle


async def plugin_send(handle, payload, stream_id):
    """Used to send the readings block from north to the configured destination.
    
    This entry point is the north plugin specific entry point that is used to 
    send data from Fledge. This will be called repeatedly with blocks of
    readings.
    
    Args:
        handle - An object which is returned by plugin_init
        payload - A List of readings block
        stream_id - An Integer that uniquely identifies the connection
                    from Fledge instance to the destination system
    Returns:
        Tuple which consists of
        - A Boolean that indicates if any data has been sent
        - The object id of the last reading which has been sent
        - Total number of readings which has been sent to the configured destination
    
    """

    # stream_id is not needed?

    try:
        plugin = handle['plugin']

        # dont try to send if the producer = None, there is no connection
        if plugin.producer:
            (is_data_sent, new_last_object_id, num_sent) = (
                await plugin.send_payloads(payload)
            )
        else:
            _LOGGER.error('Producer not available, bootstrap not connected?')
            # TODO: check what needs to be returned.
            return False, 0, 0

    except asyncio.CancelledError as err:
        _LOGGER.error(f'Asyncio cancelled: {err}')

    else:
        _LOGGER.debug('Successfully sent')
        return is_data_sent, new_last_object_id, num_sent


def plugin_shutdown(handle):
    """Used when plugin is no longer required and will be final call
    to shutdown the plugin. It should do any necessary cleanup if required.

    Part of the standard plugin interface, this will be called when the plugin
    is no longer required and will be the final call to the plugin.
  
    Sends all remaining Kafka messages and closes connection.

    Args:
         handle - Plugin handle which is returned by plugin_init
    Returns:

    """
    # should work without flushing
    # handle['plugin'].flush()
    handle['plugin'].close()
    handle['plugin'] = None

def plugin_reconfigure():
    """
    Not used in north plugins.
    """


class KafkaPlugin(object):
    """
    This class wraps the sending of the payload
    """

    def __init__(self, **config):
        """
        Initialize producer with values from json

        Args: 
            config: configuration to KafkaProducer
        Returns:

        """
        try:
            self.producer = KafkaProducer(**config)

        # TODO: no kafka errors imported, cannot use
        # except NoBrokersAvailable as e:
        # now catching general errors...
        except Exception as exc:
            _LOGGER.error(f'No Brokers?: {exc}')
            self.producer = None

        # set topic
        # TODO: hardcoded now, could be in config
        self.topic = 'Fledge'
      
    async def send_payloads(self, payloads):
        """Parse the payloads and send them

        Go through the list, transform to json.
        Send every reading on its own, at the end flush.

        Args:
            payloads: list of readings, each is a dict with:
                id:  Each reading is given an integer id that is an increasing value.
                asset_code: Asset codes are used to identify the source of the data. 
                reading: A nested dict with key-value pairs.
                ts: The timestamp when the reading was first seen by the system.
                user_ts: The timestamp of the data in the reading.

        Return:
            is_data_sent: has _any_ data been sent
            last_object_id: object id of the last reading which has been sent
            num_sent: total number of readings which has been sent

        """
        is_data_sent = False
        last_object_id = 0
        num_sent = 0

        kafka = self.producer


        def on_send_error(error):
            _LOGGER.error(f'Kafka error: {error}')


        def on_send_success(record_metadata):
            """
                https://kafka-python.readthedocs.io/en/master/usage.html#kafkaproducer
            """
            _LOGGER.debug(f'topic: {record_metadata.topic}')
            _LOGGER.debug(f'partition: {record_metadata.partition}')
            _LOGGER.debug(f'offset: {record_metadata.offset}')

        def parse_and_send(payloadToSend):
            """Format and send one payload

            Use asset as the key, so that the order stays correct in kafka.
            Kafka chooses partitions based on key, so if key is not the same
            when sending data for same thing the order might change..
            
            Args:
                payload: an item from the payloads list
            Return:

            """

            # TODO: is parsing needed?
            _LOGGER.debug(f'Payload: {payloadToSend}')
            value = json.dumps(payloadToSend['reading']).encode('utf-8')
            key = payloadToSend['asset_code']

            kafka.send(
                topic=self.topic,
                key=key.encode(),
                value=value
                ).add_callback(on_send_success).add_errback(on_send_error)
    

        try:
            for payload in payloads:
                try:
                    parse_and_send(payload)
                
                except Exception as exc:
                    # if sending was not successful, simply stop sending (return the status)
                    _LOGGER.info(f'Error with sending: {exc}')
                    break

                # has _any_ data been sent?
                else:
                    is_data_sent = True
                    last_object_id = payload['id']
                    _LOGGER.debug(f'Last sent: {last_object_id}')
                    num_sent += 1
            
        # TODO: general exception...
        except Exception as exc:
            _LOGGER.exception(f'Error in sending payloads: {exc}')

        # return in both cases
        return is_data_sent, last_object_id, num_sent
