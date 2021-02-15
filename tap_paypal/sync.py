"""Sync data."""
# -*- coding: utf-8 -*-
from datetime import datetime, timezone

import logging
from typing import Callable, Optional

import singer
from singer.catalog import Catalog

from tap_paypal.paypal import PayPal
from tap_paypal.streams import STREAMS
from tap_paypal.utils import (
    clear_currently_syncing,
    retrieve_bookmark_with_path,
    get_stream_state,
)

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
            singer.write_record(
                stream.tap_stream_id,
                row,
                time_extracted=datetime.now(timezone.utc),
            )

            if bookmark:
                # Save the bookmark to the state
                singer.write_bookmark(
                    state,
                    stream.tap_stream_id,
                    STREAMS[stream.tap_stream_id]['bookmark'],
                    bookmark,
                )

                # Clear currently syncing
                clear_currently_syncing(state)

                # Write the bootmark
                singer.write_state(state)
