#!/usr/bin/env python3

import pandas as pd
import argparse
import re

def get_county(row):
    division = row['division']
    location = row['location']
    if isinstance(division, str) and isinstance(location, str):
        if division.lower()=='california':
            county = location

            if division.lower() == 'grand princess' or location.lower() == 'grand princess cruise ship':
                return 'Grand Princess Cruise Ship'

            if 'county' in location.lower():
                county = re.search('(.+)\scounty', location.lower()).group(1)
                county = ' '.join([s.capitalize() for s in county.split()])
            if 'davis' in location.lower():
                county = 'Yolo'

            return county

    return '?'

def get_CA_lab(row):
    division = row['division']
    if division.lower()=='california':
        submitting_lab = row['submitting_lab'].strip()
        if 'Chiu Laboratory' in submitting_lab:
            # The Chiu Lab has submitted under multiple names
            return 'Chiu Laboratory, University of California, San Francisco'
        elif 'Andersen' in submitting_lab:
            # The Andersen lab has submitted under multiple names
            return 'Andersen lab at Scripps Research'
        elif submitting_lab=='Data Science':
            # These genomes are CZB genomes that were submitted by collaborators at UC Davis
            # It is unclear who the submitting lab should be, so we set it to unknown
            return 'Chan-Zuckerberg Biohub'
        elif submitting_lab=='Molecular Infectious Disease':
            # The author field indicates this is from the Andersen lab, though probably not submitted by them
            return 'Andersen lab at Scripps Research'
        elif submitting_lab=='Pathogen Discovery':
            # The CDC has submitted under multiple names
            return 'Pathogen Discovery, Respiratory Viruses Branch, Division of Viral Diseases, Centers for Disease Control and Prevention'
        return submitting_lab
    return '?'

def get_CA_region(county, regions):
    if county in list(regions['County']):
        CA_region = regions[regions['County']==county]['CA_region'].values[0]
        return CA_region
    elif county=='Grand Princess Cruise Ship':
        return 'Grand Princess Cruise Ship'
    return '?'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata', help='nextstrain metadata TSV')
    parser.add_argument('--ca_regions', help='CA regions CSV with columns County and CA_region')
    parser.add_argument('--output', help='output metadata file (default: metadata.tsv)', default='metadata.tsv')
    
    args = parser.parse_args()

    meta = pd.read_csv(args.metadata, sep='\t')
    meta['county'] = meta.apply(get_county, axis=1)
    meta['CA_lab'] = meta.apply(get_CA_lab, axis=1)
    regions = pd.read_csv(args.ca_regions)
    meta['CA_region'] = meta['county'].apply(get_CA_region, regions=regions)

    meta.to_csv(args.output, sep='\t', index=False)

if __name__ == '__main__':
    main()