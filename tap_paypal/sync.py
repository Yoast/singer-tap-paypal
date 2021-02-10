"""Sync data."""
# -*- coding: utf-8 -*-

from typing import Callable
import logging
from pprint import pprint
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
    LOGGER.info('Current state:')
    LOGGER.info(state)

    # Set currently syncing
    for stream_name, stream_state in state.get('bookmarks', {}).items():
        LOGGER.info(f'Stream name: {stream_name} --> state: {stream_state}')
        singer.set_currently_syncing(state, stream_name)

    LOGGER.info('Write state')
    singer.write_state({"test": 123})

    LOGGER.info('Selected streams are now:')
    LOGGER.info(list(catalog.get_selected_streams(state)))


    #for stream in catalog.get_selected_streams(state):
    for stream in catalog.streams:
        LOGGER.info(f'Syncing stream: {stream.tap_stream_id}')

        # Get the state
        stream_state: dict = state.get(
            'bookmarks',
            {},
        ).get(stream.tap_stream_id)

        LOGGER.info(stream_state)

        bookmark_column = stream.replication_key
        LOGGER.info(f'Bookbmark column: {bookmark_column}')
        is_sorted: bool = True  # TODO: indicate whether data is sorted ascending on bookmark value

        LOGGER.info(stream.key_properties)

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        # TODO: delete and replace this inline function with your own data retrieval process:
        # tap_data = lambda: [{"id": x, "name": "row${x}"} for x in range(1000)]

        # Every stream has a corresponding method in the PayPal object e.g.:
        # The stream paypal_transactions will call paypal.paypal_transactions
        tap_data: Callable = getattr(paypal, stream.tap_stream_id)

        max_bookmark = None

        # The tap_data method yields rows of data from the API
        # The state of the stream is used as kwargs for the method
        # # E.g. start_date='2021-01-01T00:00:00+0000'
        for row in tap_data(**stream_state):
            # TODO: place type conversions or transformations here
            pprint(row)
            


            # write one or more rows to the stream:
            singer.write_records(stream.tap_stream_id, [row])
            if bookmark_column:
                if is_sorted:
                    # update bookmark to latest value
                    singer.write_state(
                        {stream.tap_stream_id: row[bookmark_column]},
                    )
                else:
                    # if data unsorted, save max value until end of writes
                    max_bookmark = max(max_bookmark, row[bookmark_column])

            break
        if bookmark_column and not is_sorted:
            singer.write_state({stream.tap_stream_id: max_bookmark})
