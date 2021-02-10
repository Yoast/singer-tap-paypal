"""Sync data."""
# -*- coding: utf-8 -*-

import logging
from functools import reduce
from typing import Callable, Optional

import singer
from singer.catalog import Catalog

from tap_paypal.paypal import PayPal

LOGGER: logging.RootLogger = singer.get_logger()


def sync(
    paypal: PayPal,
    state: dict,
    catalog: Catalog,
    start_date: str,
) -> None:
    """Sync data from tap source.

    Arguments:
        paypal {PayPal} -- PayPal client
        state {dict} -- Tap state
        catalog {Catalog} -- Stream catalog
        start_date {str} -- Start date
    """
    # For every stream in the catalog
    LOGGER.info('Sync')
    LOGGER.debug('Current state:\n{state}')

    # Only selected streams are synced, whether a stream is selected is
    # determined by whether the key-value: "selected": true is in the schema
    # file.
    for stream in catalog.get_selected_streams(state):
        LOGGER.info(f'Syncing stream: {stream.tap_stream_id}')

        # Update the current stream as active syncing in the state
        singer.set_currently_syncing(state, stream.tap_stream_id)

        # Retrieve the state of the stream
        stream_state: dict = get_stream_state(state, stream.tap_stream_id)

        LOGGER.debug(f'Stream state: {stream_state}')

        # Write the schema
        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        # Every stream has a corresponding method in the PayPal object e.g.:
        # The stream: paypal_transactions will call: paypal.paypal_transactions
        tap_data: Callable = getattr(paypal, stream.tap_stream_id)

        # The tap_data method yields rows of data from the API
        # The state of the stream is used as kwargs for the method
        # E.g. if the state of the stream has a key 'start_date', it will be
        # used in the method as start_date='2021-01-01T00:00:00+0000'
        for row in tap_data(**stream_state):
            # Retrieve the value of the bootmark
            bookmark: Optional[str] = retrieve_bookmark_with_path(
                stream.replication_key,
                row,
            )

            # Write a row to the stream
            singer.write_records(stream.tap_stream_id, [row])

            if bookmark:
                # Save the bookmark to the state
                singer.write_state(
                    {stream.tap_stream_id: bookmark},
                )


def retrieve_bookmark_with_path(path: str, row: dict) -> Optional[str]:
    """The bookmark exists in the row of data which is an dictionary. However,
    the bookmark can either be a key such as row[key] but also a subkey such as
    row[key][subkey]. In the streams definition file, the key can be saved as
    a string, but [key][subkey] cannot. Therefore, in the streams file, if we
    want to use a subkey as bookmark, we save it in the format 'key.subkey',
    which is our path in the dictionary.
    This helper function parses the string and checks whether it has a dot.
    If it has one, it returns the value of the subkey in the row of data, e.g.
    row[key][subkey]. If not it returns the alue of the key, e.g row[path].

    Arguments:
        path {str} -- Path in the dictionary
        row {dict} -- Data row

    Returns:
        Optional[str] -- The value or from the key or subkey
    """
    # If the path has a dot, then parse it as key and subkeys
    if '.' in path:
        return str(reduce(dict.get, path.split('.'), row))  # type: ignore
    # Else if the path is just a key, parse it as a normal key
    elif path:
        return row[path]
    return None


def get_stream_state(state: dict, tap_stream_id: str) -> dict:
    """Return the state of the stream.

    Arguments:
        state {dict} -- The state
        tap_stream_id {str} -- The id of the stream

    Returns:
        dict -- The state of the stream
    """
    return state.get(
            'bookmarks',
            {},
        ).get(tap_stream_id)
