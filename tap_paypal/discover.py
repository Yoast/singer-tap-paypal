"""Discover."""
# -*- coding: utf-8 -*-
from singer import metadata
from singer.catalog import Catalog, CatalogEntry

from tap_paypal.schema import load_schemas
from tap_paypal.streams import STREAMS


def discover() -> Catalog:  # noqa: WPS210
    """Load the Stream catalog.

    Returns:
        Catalog -- The catalog
    """
    raw_schemas: dict = load_schemas()
    streams: list = []

    # For every schema
    for stream_id, schema in raw_schemas.items():

        mdata = metadata.get_standard_metadata(
            schema=schema.to_dict(),
            key_properties=STREAMS[stream_id].get('key_properties', None),
            valid_replication_keys=STREAMS[stream_id].get(
                'replication_keys',
                None,
            ),
            replication_method=STREAMS[stream_id].get(
                'replication_method',
                None,
            ),
        )

        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=STREAMS[stream_id].get('key_properties', None),
                metadata=mdata,
                replication_key=STREAMS[stream_id].get(
                    'replication_key',
                    None,
                ),
                replication_method=STREAMS[stream_id].get(
                    'replication_method',
                    None,
                ),
            ),
        )
    return Catalog(streams)
