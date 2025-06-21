import codecs
import copy
import datetime
import json
import os
import uuid as GenUUID


from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.types import JSON, Float, Text, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB


# Note, the database credentials in the DB URL are set to the default values for a local Arches install, 
# these should be changed to match your own database and set with the ARCHES_DB_URL environment variable.
ARCHES_DB_URL = os.getenv('ARCHES_DB_URL', 'postgresql://postgres:postgis@127.0.0.1:5434/afs_demo')

ARCHES_V8 = False
# UUID of the resource_instance_lifecycle_state_id for the Arches 8.0.0 release
ARCHES_V8_RESOURCE_INSTANCE_LIFECYCLE_STATE_ID = '7e3cce56-fbfb-4a4b-8e83-59b9f9e7cb75'
# ARCHES_V8_RESOURCE_INSTANCE_LIFECYCLE_STATE_ID =  '9375c9a7-dad2-4f14-a5c1-d7e329fdde4f'

current_directory = os.getcwd()
DATA_DIR = os.getenv('AFS_ETL_DIR', os.path.join(current_directory, 'data'))
RAW_IMPORT_CSV = os.path.join(DATA_DIR, 'oc-sherd-data.csv')
ARCHES_INSERT_SQL_PATH =  os.path.join(DATA_DIR, 'etl_sql.txt')

STAGING_SCHEMA_NAME = 'staging'


GRAPH_PUBLICATION_ID = '8316a878-4c8f-11f0-be9e-020539808477'

# The UUID for the English language value. This is the prefLabel relates to the
# English concept (id: '38729dbe-6d1c-48ce-bf47-e2a18945600e')
ENG_VALUE_UUID = 'bc35776b-996f-4fc1-bd25-9f6432c1f349'
UNDET_LANG_VALUE_UUID = 'dcfb76cd-dd1e-4d45-bb0a-d0f9de3e1b8f'

# These UUIDs are actually for the prefLabel value that is related to the concepts
# for these types... Again, a reminder about this likely point of confusion.
PRIMARY_NAME_TYPE_UUID = 'e7d4b0bf-f37a-4af3-aa0b-4f63152ef9f6'
PREFERRED_TERM_TYPE_UUID = '8f40c740-3c02-4839-b1a4-f1460823a9fe'
ALT_NAME_TYPE_UUID = '0798bf2c-ab07-43d7-81f4-f1e2d20251a1'

PRIMARY_ID_TYPE_VALUE_UUID = 'ae7f2811-3fee-4624-bc74-9451bd05be2d'



TILE_DATA_COPY_FLAG = '----COPY:stage_targ_field----'


DATA_TYPES_SQL = {
    JSONB: 'jsonb',
    UUID: 'uuid',
    Integer: 'integer',
    Float: 'float',
    Numeric: 'numeric',
    Text: 'text',
    DateTime: 'timestamp',
    ARRAY(UUID): 'uuid[]',
}


REL_LINK_REL_TYPE_ID = 'ac41d9be-79db-4256-b368-2f4559cfbe55'
REL_LINK_INVERSE_REL_TYPE_ID = 'ac41d9be-79db-4256-b368-2f4559cfbe55'



def copy_value(value):
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if isinstance(value, list):
        return copy.deepcopy(value)
    return value

def make_lang_dict_value(value, lang='en'):
    return {
        lang: {
            'value': str(value),
            'direction': 'ltr',
        }
    }

def make_empty_dict(value):
    return {}


# For this demo, we're using the AfRSC resource and sample collection resource model.
# Alter this as needed to fit your own
PHYS_UUID = '9519cb4f-b25b-11e9-8c7b-a4d18cec433a'
PHYS_MODEL_NAME = 'physical_thing'


PHYS_NAME_TILE_DATA = {
    "b9c1d7ab-b497-11e9-9ab7-a4d18cec433a": [PREFERRED_TERM_TYPE_UUID, PRIMARY_NAME_TYPE_UUID,], # type
    "b9c1d570-b497-11e9-8315-a4d18cec433a": None, # source
    "b9c1d69e-b497-11e9-8408-a4d18cec433a": None, # _label
    "b9c1d400-b497-11e9-90ea-a4d18cec433a": [UNDET_LANG_VALUE_UUID,], # language
    "b9c1d8a6-b497-11e9-876b-a4d18cec433a": TILE_DATA_COPY_FLAG,
}


PHYS_NAME_IDS_MAPPING_CONFIGS = {
    'model_id': PHYS_UUID,
    'staging_table': 'phys_name_ids',
    'model_staging_schema': PHYS_MODEL_NAME,
    'raw_pk_col': 'item_uuid',
    'mappings': [
        {
            'raw_col': 'item_uuid',
            'targ_table': 'instances',
            'stage_field_prefix': '',
            'value_transform': copy_value,
            'targ_field': 'resourceinstanceid',
            'data_type': UUID,
            'make_tileid': False,
            'default_values': [
                ('graphid', UUID, PHYS_UUID,),
                ('graphpublicationid', UUID, GRAPH_PUBLICATION_ID,),
                ('principaluser_id', Integer, 1,),
            ],
            'make_descriptor': {
                'raw_name_col': 'Item Label',
                'description': 'A pottery sherd characterized by Neutron Activation Analysis (NAA)',
                'map_popup': 'Recovered in excavation',
            },
            'make_name': {
                'raw_name_col': 'Item Label',
            },
        },
        {
            'raw_col': 'Item Label',
            'targ_table': 'name',
            'stage_field_prefix': 'item_label_',
            'value_transform': make_lang_dict_value,
            'targ_field': 'name_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('name_type_', ARRAY(UUID), [PREFERRED_TERM_TYPE_UUID, PRIMARY_NAME_TYPE_UUID ],),
                ('name_language_', ARRAY(UUID), [UNDET_LANG_VALUE_UUID],),
                ('nodegroupid', UUID, 'b9c1ced7-b497-11e9-a4da-a4d18cec433a',),
            ],
            'tile_data': PHYS_NAME_TILE_DATA, 
        },
        {
            'raw_col': 'URI',
            'targ_table': 'identifier',
            'stage_field_prefix': 'id_uri_',
            'value_transform': make_lang_dict_value,
            'targ_field': 'identifier_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('identifier_type', ARRAY(UUID), [PRIMARY_ID_TYPE_VALUE_UUID],),
                ('nodegroupid', UUID, '22c150ca-b498-11e9-9adc-a4d18cec433a',),
            ],
        },
        {
            'raw_col': 'Citation URI',
            'targ_table': 'identifier',
            'stage_field_prefix': 'id_ark_',
            'value_transform': make_lang_dict_value,
            'targ_field': 'identifier_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('identifier_type', ARRAY(UUID),  [PRIMARY_ID_TYPE_VALUE_UUID],),
                ('nodegroupid', UUID, '22c150ca-b498-11e9-9adc-a4d18cec433a',),
            ],
        },
    ],
}






DIG_RES_UUID = '707cbd78-ca7a-11e9-990b-a4d18cec433a'
DIG_RES_MODEL_NAME = 'digital_resources'

IMPORT_IMAGES_CSV = os.path.join(DATA_DIR, 'oc-sherd-images.csv')

DIG_RES_NAME_TILE_DATA = {
    "d2fdc0d4-ca7a-11e9-95cf-a4d18cec433a": [PREFERRED_TERM_TYPE_UUID, PRIMARY_NAME_TYPE_UUID,], # type
    "d2fdbc38-ca7a-11e9-a31a-a4d18cec433a": None, # source
    "d2fdbeb8-ca7a-11e9-a294-a4d18cec433a": None, # _label
    "d2fdb92b-ca7a-11e9-af41-a4d18cec433a": [ENG_VALUE_UUID,], # language
    "d2fdc2fa-ca7a-11e9-8ffb-a4d18cec433a": TILE_DATA_COPY_FLAG,
}




DIG_RES_IDS_MAPPING_CONFIGS = {
    'model_id': DIG_RES_UUID,
    'staging_table': 'dig_res_name_ids_rels',
    'model_staging_schema': DIG_RES_MODEL_NAME,
    'raw_pk_col': 'media_uuid',
    'load_path': IMPORT_IMAGES_CSV,
    'mappings': [
        {
            'raw_col': 'media_uuid',
            'targ_table': 'instances',
            'stage_field_prefix': '',
            'value_transform': copy_value,
            'targ_field': 'resourceinstanceid',
            'data_type': UUID,
            'make_tileid': False,
            'default_values': [
                ('graphid', UUID, DIG_RES_UUID,),
                ('graphpublicationid', UUID, GRAPH_PUBLICATION_ID,),
                ('principaluser_id', Integer, 1,),
            ],
            'make_descriptor': {
                'raw_name_col': 'media_label',
                'description': 'Photo of a pottery sherd characterized by Neutron Activation Analysis (NAA)',
                'map_popup': 'Recovered in excavation',
            },
            'make_name': {
                'raw_name_col': 'media_label',
            }, 
        },
        {
            'raw_col': 'media_label',
            'targ_table': 'name',
            'stage_field_prefix': 'media_label_',
            'value_transform': make_lang_dict_value,
            'targ_field': 'name_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('name_type', ARRAY(UUID), [PREFERRED_TERM_TYPE_UUID, PRIMARY_NAME_TYPE_UUID ],),
                ('name_language', ARRAY(UUID), [ENG_VALUE_UUID],),
                ('nodegroupid', UUID, 'd2fdae3d-ca7a-11e9-ad84-a4d18cec433a',),
            ],
            'tile_data': DIG_RES_NAME_TILE_DATA,  
        },
        {
            'raw_col': 'media_ark',
            'targ_table': 'identifier',
            'stage_field_prefix': 'id_ark_',
            'value_transform': make_lang_dict_value,
            'targ_field': 'identifier_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('identifier_type', ARRAY(UUID),  [PRIMARY_ID_TYPE_VALUE_UUID],),
                ('nodegroupid', UUID, '22c150ca-b498-11e9-9adc-a4d18cec433a',),
            ],
        },
        {
            'raw_col': 'media_type_afs_uuid',
            'targ_table': 'type',
            'stage_field_prefix': 'type_',
            'value_transform': copy_value,
            'targ_field': 'type',
            'data_type': ARRAY(UUID),
            'make_tileid': True,
            'default_values': [
                ('nodegroupid', UUID, '09c1778a-ca7b-11e9-860b-a4d18cec433a',),
            ],
        },
        {
            'raw_col': 'file_id',
            'targ_table': 'file',
            'stage_field_prefix': 'file_',
            'value_transform': copy_value,
            'targ_field': 'file',
            'data_type': JSONB,
            'make_tileid': True,
            'make_file': {
                'raw_filename_col': 'afs_filename',
                'raw_file_id_col': 'file_id',
                'raw_filesize_col': 'filesize',
                'mimetype': 'image/jpeg',
            },
            'default_values': [
                ('nodegroupid', UUID, '09c1778a-ca7b-11e9-860b-a4d18cec433a',),
            ],
        },
    ],
}


PHYS_REL_DIG_RES_MAPPING_CONFIGS = {
    'model_id': PHYS_UUID,
    'staging_table': 'phys_rel_dig_res',
    'model_staging_schema': PHYS_MODEL_NAME,
    'raw_pk_col': 'item_uuid',
    'load_path': IMPORT_IMAGES_CSV,
    'mappings': [
        {
            'raw_col': 'item_uuid',
            'targ_table': 'instances',
            'stage_field_prefix': '',
            'value_transform': copy_value,
            'targ_field': 'resourceinstanceid',
            'data_type': UUID,
            'make_tileid': False,
            'default_values': [
                ('graphid', UUID, PHYS_UUID,),
                ('graphpublicationid', UUID, GRAPH_PUBLICATION_ID,),
                ('principaluser_id', Integer, 1,),
            ], 
        },
        {
            'raw_col': 'dig_ref_media_type_afs_uuid',
            'targ_table': 'digital_reference',
            'stage_field_prefix': 'type_',
            'value_transform': copy_value,
            'targ_field': 'digital_reference_type',
            'data_type': UUID,
            'make_tileid': True,
            'default_values': [
                ('nodegroupid', UUID, '8a4ad932-8d59-11eb-a9c4-faffc265b501',),
            ],
            'related_resources': [
                {
                    'group_source_field': 'digital_source_',
                    'multi_value': True,
                    'targ_field': 'digital_source',
                    'source_field_from_uuid': 'resourceinstanceid',
                    'source_field_to_uuid': 'media_uuid',
                    'rel_type_id': 'be3f33e9-216d-4355-8766-aced1e95616c',
                    'inverse_rel_type_id': 'ff6a0510-6c91-4c45-8c67-dbbcf8d7d7fa',
                    'rel_nodeid': 'a298ee52-8d59-11eb-a9c4-faffc265b501',
                },
            ],
        },
    ],
}


ALL_MAPPING_CONFIGS = [
    # Create resource instances for different models
    PHYS_NAME_IDS_MAPPING_CONFIGS,
    DIG_RES_IDS_MAPPING_CONFIGS,
    PHYS_REL_DIG_RES_MAPPING_CONFIGS,
]




ARCHES_REL_VIEW_PREP_SQLS = [
    f"""
    SELECT __arches_create_resource_model_views('{PHYS_UUID}');
    """,
    f"""
    SELECT __arches_create_resource_model_views('{DIG_RES_UUID}');
    """,
]
