import json
import pandas as pd
import uuid as GenUUID

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import RDFS, SKOS, DCTERMS


from arches_afs import general_configs
from arches_afs import utilities


"""
# testing

from arches_afs import general_configs
from arches_afs import project_set
df_done = project_set.prepare_save_projs_sets_data()


"""

# key is the open context project UUID, va;lue is the AFS project UUID
OC_TO_AFS_PROJ_UUIDS = {
    'cbd24bbb-c6fc-44ed-bd67-6f844f120ad5': '44ee8aed-d3cd-4ec7-b7d3-a9926e03a0d0', # Sardis
    '81d1157d-28f4-46ff-98dd-94899c1688f8': '62881482-c448-4dfc-b142-6db23c52ec8d', # Kinet Höyük
    '45c12f7c-8744-47bb-902a-523d11ce0c32': '2bc523c8-6d65-47c1-ad1e-1a8efd974c42', # Troy
}

# key is the open context project UUID, va;lue is the AFS set UUID
OC_TO_AFS_SET_UUIDS = {
    'cbd24bbb-c6fc-44ed-bd67-6f844f120ad5': '462ee9b0-9bf7-49af-aeff-80a17f280e51', # Sardis
    '81d1157d-28f4-46ff-98dd-94899c1688f8': '73583e33-9f30-4076-aa27-6c7282e9d90e', # Kinet Höyük
    '45c12f7c-8744-47bb-902a-523d11ce0c32': 'c0debb27-0791-4a83-bd33-77c5d66bffc2', # Troy
}

AFS_PROJ_TO_SET_UUIDS = {
    '44ee8aed-d3cd-4ec7-b7d3-a9926e03a0d0': '462ee9b0-9bf7-49af-aeff-80a17f280e51', # Sardis
    '62881482-c448-4dfc-b142-6db23c52ec8d': '73583e33-9f30-4076-aa27-6c7282e9d90e', # Kinet Höyük
    '2bc523c8-6d65-47c1-ad1e-1a8efd974c42': 'c0debb27-0791-4a83-bd33-77c5d66bffc2', # Troy
}


AFS_PROJ_TO_STATEMENTS = {
    '44ee8aed-d3cd-4ec7-b7d3-a9926e03a0d0': (
        'This sherd was recovered during archaeological excavations at Sardis '
        'and the was selected for study using Neutron Activation Analysis (NAA). '
    ),
    '62881482-c448-4dfc-b142-6db23c52ec8d': (
        'This sherd was recovered during archaeological excavations at Kinet Höyük '
        'and the was selected for study using Neutron Activation Analysis (NAA). '
    ),
    '2bc523c8-6d65-47c1-ad1e-1a8efd974c42': (
        'This sherd was recovered during archaeological excavations at Troy '
        'and the was selected for study using Neutron Activation Analysis (NAA). '
    ),
}

def prep_projs_sets_data(df):
    keep_cols = [
        'item_uuid', 
        'Item Label', 
        'Arches Project UUID',
    ]
    df_done = df[keep_cols].copy()
    df_done['set_uuid'] = df_done['Arches Project UUID'].apply(
        lambda x: AFS_PROJ_TO_SET_UUIDS.get(x, '')
    )
    df_done['set_statement'] = df_done['Arches Project UUID'].apply(
        lambda x: AFS_PROJ_TO_STATEMENTS.get(x, ('', ''))
    )
    # Add the type information for pottery (visual works)
    type_json_str = json.dumps(
       [general_configs.POTTERY_VALUE_ID]
    )
    df_done['type_uuids'] = type_json_str
     # Add the member of nodegroup uuid
    df_done['member_of_nodegroupid'] = general_configs.MEMBER_OF_NODEGROUP_UUID 
    return df_done


def prepare_save_projs_sets_data(
    df=None, 
    raw_path=general_configs.RAW_IMPORT_CSV, 
    save_path=general_configs.IMPORT_PROJ_SETS_CSV,
):
    if df is None:
        df = pd.read_csv(raw_path)
    df_done = prep_projs_sets_data(df)
    df_done.to_csv(save_path, index=False)
    return df_done