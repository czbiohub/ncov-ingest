#!/usr/bin/env python3

import argparse
import pandas as pd
import re
from Bio import SeqIO
import warnings


def rename_sample(seq: SeqIO.SeqRecord, df: pd.DataFrame, logfile) -> SeqIO.SeqRecord:
    """
    Rename samples according to their GISAID IDs.
    """
    try:
        publicID = df[df['sample_name']==seq.id]['gisaid_name'].values[0]
        publicID = '/'.join(publicID.split('/')[1:])
    except IndexError:
        logfile.write(f'{seq.id}\n')
        return None
    seq.id = publicID
    seq.name = publicID
    seq.description = publicID
    return seq

def combine_metadata(nextstrain_meta: pd.DataFrame, sample_meta: pd.DataFrame) -> pd.DataFrame:
    """
    Combine sample metadata with previous existing metadata.
    """
    df = pd.concat([nextstrain_meta, sample_meta],
                    axis=0,
                    join='outer',
                    sort=False)

    # Drop duplicate strains and only keep the first row from nextstrain_meta
    df = df.drop_duplicates(subset='strain')
    df = df.fillna('?')
    return df

def main():
    parser = argparse.ArgumentParser(description='Prepare ncov pipeline input from genome assembly pipeline output.')
    parser.add_argument('--combined_fa', help='combined.fa')
    parser.add_argument('--combined_tsv', help='combined.stats.tsv')
    parser.add_argument('--minLength', help='minimum n_actg', default=29000, type=int)
    parser.add_argument('--maxNs', help='maximum Ns', default=1000, type=int)
    parser.add_argument('--maxAmbiguous', help='maximum ambiguous bases', default=1000, type=int)
    parser.add_argument('--gisaid_names', help='submitted_sequences.tsv with GISAID IDs and sample names.')
    parser.add_argument('--sample_meta', help='Prepared sample metadata for nextstrain.')
    parser.add_argument('--nextstrain_meta', help='Metadata for non-sample sequences.')
    parser.add_argument('--nextstrain_sequences', help='Non-sample sequences FASTA.')
    parser.add_argument('--prefix', help='output prefix')
    parser.add_argument('--missing_ids', help='file to output sequences missing a GISAID name', default='missing_ids.txt')
    parser.add_argument('--missing_metadata', help='file to output sequences missing metadata', default='missing_metadata.txt')

    args = parser.parse_args()

    if args.prefix:
        prefix = args.prefix + '_'
    else:
        prefix = ""

    ns_meta = pd.read_csv(args.nextstrain_meta, sep='\t')
    sample_meta = pd.read_csv(args.sample_meta, sep='\t')

    meta = combine_metadata(ns_meta, sample_meta)

    meta.to_csv(prefix + 'metadata.tsv', sep='\t', index=False)
    print(f'Metadata written to {prefix}metadata.tsv')

    combined_sequences = SeqIO.parse(args.combined_fa, 'fasta')
    combined_stats = pd.read_csv(args.combined_tsv, sep='\t')
    filtered_stats = combined_stats[(combined_stats['n_actg']>=args.minLength) & (combined_stats['n_missing']<args.maxNs) & (combined_stats['n_ambiguous']<args.maxAmbiguous)]
    sample_sequences = [s for s in combined_sequences if s.id in list(filtered_stats['sample_name'])]

    gisaid_names = pd.read_csv(args.gisaid_names, sep='\t')
    with open(args.missing_ids, 'w+') as f:
        renamed_sequences = [rename_sample(s, gisaid_names, f) for s in sample_sequences]
    renamed_sequences = [s for s in renamed_sequences if s]
    renamed_ids = set(s.id for s in renamed_sequences)
    sample_ids = set(s.id for s in sample_sequences)
    if renamed_ids.intersection(sample_ids):
        warnings.warn(f'Not all sequences have been renamed, check {args.missing_ids} and that input TSV matches the sample names.')
    
    no_metadata = [s.id for s in sample_sequences if s.id not in list(meta['strain'])]
    with open(args.missing_metadata, 'w+') as f:
        for i in no_metadata:
            f.write(f'{i}\n')
    if no_metadata:
        warnings.warn(f'Not all sequences have metadata, check {args.missing_metadata} and that the sample metadata contains all sequences.')

    SeqIO.write(renamed_sequences, prefix + 'renamed_sequences.fasta', 'fasta')
    print(f'Renamed sequences written to {prefix}renamed_sequences.fasta')

if __name__ == '__main__':
    main()


