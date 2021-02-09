"""Discover."""
# -*- coding: utf-8 -*-
from singer.catalog import Catalog, CatalogEntry
from tap_paypal.schema import load_schemas
from singer import metadata


def discover() -> Catalog:  # noqa: WPS210
    """Load the Stream catalog.

    Returns:
        Catalog -- The catalog
    """
    raw_schemas: dict = load_schemas()
    streams: list = []

    # For every schema
    for stream_id, schema in raw_schemas.items():

        # mdata = metadata.new()
        # mdata = metadata.get_standard_metadata(
        #     schema=schema,
        #     key_properties=None,
        #     valid_replication_keys=None,
        #     replication_method=None,
        # )

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
