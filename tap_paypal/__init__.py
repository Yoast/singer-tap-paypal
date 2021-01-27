"""PayPal tap."""
# -*- coding: utf-8 -*-
import json
import logging
import os
from argparse import Namespace

import singer
from singer import metadata, utils
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema

REQUIRED_CONFIG_KEYS: tuple = ('start_date', 'username', 'password')
LOGGER: logging.RootLogger = singer.get_logger()


def get_abs_path(path: str) -> str:
    """Help function to get the absolute path.

    Arguments:
        path {str} -- Path to directory

    Returns:
        str -- The absolute path
    """
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path,
    )


def load_schemas() -> dict:
    """Load schemas from schemas folder.

    Returns:
        dict -- Scemas
    """
    schemas: dict = {}

    # For every file in the schemas directory
    for filename in os.listdir(get_abs_path('schemas')):
        abs_path: str = get_abs_path('schemas')
        path: str = f'{abs_path}/{filename}'
        file_raw: str = filename.replace('.json', '')

        # Open and load the schema
        with open(path) as schema_file:
            schemas[file_raw] = Schema.from_dict(json.load(schema_file))
    return schemas


def discover():
    raw_schemas: dict = load_schemas()
    streams: list = []

    # For every schema
    for stream_id, schema in raw_schemas.items():

        # TODO: populate any metadata and stream's key properties here..
        stream_metadata: list = []
        key_properties: list = []
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            ),
        )
    return Catalog(streams)


def sync(config: dict, state: dict, catalog: Catalog) -> None:
    """Sync data from tap source.

    Arguments:
        config {dict} -- Config from json file
        state {dict} -- Tap state
        catalog {Catalog} -- Stream catalog
    """
    # For every stream in the catalog
    for stream in catalog.get_selected_streams(state):
        LOGGER.info(f'Syncing stream: {stream.tap_stream_id}')

        bookmark_column = stream.replication_key
        is_sorted: bool = True  # TODO: indicate whether data is sorted ascending on bookmark value

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema,
            key_properties=stream.key_properties,
        )

        # TODO: delete and replace this inline function with your own data retrieval process:
        tap_data = lambda: [{"id": x, "name": "row${x}"} for x in range(1000)]

        max_bookmark = None

        # For every row in the tap data
        for row in tap_data():
            # TODO: place type conversions or transformations here

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
        if bookmark_column and not is_sorted:
            singer.write_state({stream.tap_stream_id: max_bookmark})


@utils.handle_top_exception(LOGGER)
def main() -> None:
    """Run tap."""
    # Parse command line arguments
    args: Namespace = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog: Catalog = discover()
        catalog.dump()
        return

    # Otherwise run in sync mode
    if args.catalog:
        # Load command line catalog
        catalog = args.catalog
    else:
        # Loadt the  catalog
        catalog = discover()

    sync(args.config, args.state, catalog)


if __name__ == '__main__':
    main()
