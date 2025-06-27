import json
import pandas as pd
import uuid as GenUUID

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import RDFS, SKOS, DCTERMS


from arches_afs import general_configs
from arches_afs import project_set
from arches_afs import utilities


"""
# testing

from arches_afs import general_configs
from arches_afs import places
df_rel = places.prepare_save_places_and_rels_data()


"""




AFS_PROJ_TO_PLACES = {
    '44ee8aed-d3cd-4ec7-b7d3-a9926e03a0d0': {
        'place_uuid': '3b3386a8-0867-4563-89b1-081f5e2b87b6',
        'place_name': 'Sardis',
        'place_statement': 'An archaeological site in modern Türkiye (Turkey).',
        'place_uri': 'https://pleiades.stoa.org/places/550867',
    },
    '62881482-c448-4dfc-b142-6db23c52ec8d': {
        'place_uuid': '57f2bf9c-ce32-494e-9c16-67ad23d069cb',
        'place_name': 'Kinet Höyük',
        'place_statement': (
            'An archaeological site in modern Türkiye (Turkey), '
            'which was the ancient port of Issus/Nikopolis.'
        ),
        'place_uri': 'https://pleiades.stoa.org/places/658490',
    },
    '2bc523c8-6d65-47c1-ad1e-1a8efd974c42': {
        'place_uuid': 'ac2067dd-a25d-4eda-9406-33089b1ee111',
        'place_name': 'Troy',
        'place_statement': (
            'An archaeological site in modern Türkiye (Turkey), '
            'with occupation ranging from the Bronze Age to the Roman period. '
            'Troy features as the central setting of Homer\'s Iliad.'
        ),
        'place_uri': 'https://pleiades.stoa.org/places/550595',
    },
}


def prep_phys_places_rel_data(df):
    """Make a dataframe to relate Physical samples and places"""
    keep_cols = [
        'item_uuid', 
        'Item Label', 
        'Arches Project UUID',
        'geo_point',
    ]
    df_rel = df[keep_cols].copy()
    df_rel['set_uuid'] = ''
    df_rel['place_uuid'] = ''
    df_rel['add_collection_types_uuid'] = json.dumps(general_configs.ADD_TO_COLLECTION_TYPE_VALUE_IDS)
    df_rel['add_statement'] = ''
    for proj_id, place_dict in AFS_PROJ_TO_PLACES.items():
        prj_index = df['Arches Project UUID'] == proj_id
        df_rel.loc[prj_index, 'set_uuid'] = project_set.AFS_PROJ_TO_SET_UUIDS.get(proj_id)
        df_rel.loc[prj_index, 'add_statement'] = project_set.AFS_PROJ_TO_STATEMENTS.get(proj_id)
        df_rel.loc[prj_index, 'place_uuid'] = place_dict.get('place_uuid')
    return df_rel


def prep_df_places(df):
    """Make a dataframe of places"""
    data_rows = []
    for proj_id, place_dict in AFS_PROJ_TO_PLACES.items():
        prj_index = df['Arches Project UUID'] == proj_id
        geo_point = df[prj_index]['geo_point'].iloc[0]
        place_dict['geo_point'] = geo_point
        data_rows.append(place_dict)
    df_places = pd.DataFrame(data_rows)
    return df_places


def prepare_save_places_and_rels_data(
    df=None, 
    raw_path=general_configs.RAW_IMPORT_CSV, 
    place_path=general_configs.IMPORT_PLACES_CSV,
    rel_path=general_configs.IMPORT_REL_PHYS_PLACES,
):
    if df is None:
        df = pd.read_csv(raw_path)
    df_places = prep_df_places(df)
    df_places.to_csv(place_path, index=False)
    df_rel = prep_phys_places_rel_data(df)
    df_rel.to_csv(rel_path, index=False)
    return df_rel