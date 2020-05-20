#!/usr/bin/env python3
import pandas as pd

def hierarchy_dataframe(metadata: pd.DataFrame, hierarchy_columns: list) -> pd.DataFrame:
    """
    Given a ``pd.DataFrame`` `metadata`, returns a `pd.DataFrame` with one row
    for every unique location hierarchy defined by the `hierarchy_columns` (e.g.
    region, country, and division). Looks for location columns matching the
    original resolution name (e.g. 'region') and any stubname of it (e.g.
    'region_exposure').
    """
    metadata = metadata.rename(columns={
        resolution: f'{resolution}_strain' for resolution in hierarchy_columns
    })

    return pd \
        .wide_to_long(metadata,
            stubnames=hierarchy_columns,
            i=['gisaid_epi_isl', 'strain'],
            j="resolution_type",
            sep='_',
            suffix='\w+') \
        .reset_index()[hierarchy_columns] \
        .fillna('') \
        .drop_duplicates() \
        .reset_index(drop=True) \
        .sort_values(by=hierarchy_columns)
