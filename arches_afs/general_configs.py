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
ARCHES_DB_URL = os.getenv('ARCHES_DB_URL', 'postgresql://postgres:postgis@127.0.0.1:5434/rascoll')

ARCHES_V8 = False
# UUID of the resource_instance_lifecycle_state_id for the Arches 8.0.0 release
ARCHES_V8_RESOURCE_INSTANCE_LIFECYCLE_STATE_ID = '7e3cce56-fbfb-4a4b-8e83-59b9f9e7cb75'
# ARCHES_V8_RESOURCE_INSTANCE_LIFECYCLE_STATE_ID =  '9375c9a7-dad2-4f14-a5c1-d7e329fdde4f'

current_directory = os.getcwd()
DATA_DIR = os.getenv('AFS_ETL_DIR', os.path.join(current_directory, 'data'))
RAW_IMPORT_CSV = os.path.join(DATA_DIR, 'gci-all-orig.csv')
ARCHES_INSERT_SQL_PATH =  os.path.join(DATA_DIR, 'etl_sql.txt')

STAGING_SCHEMA_NAME = 'staging'

# For this demo, we're using the AfRSC resource and sample collection resource model.
# Alter this as needed to fit your own
PHYS_UUID = ''
PHYS_MODEL_NAME = 'physical_thing'




PHYS_MAPPING_CONFIGS = {
    'model_id': PHYS_UUID,
    'staging_table': 'phys',
    'model_staging_schema': PHYS_MODEL_NAME,
    'raw_pk_col': 'phys_uuid',
    'mappings': [
        {
            'raw_col': 'phys_uuid',
            'targ_table': 'instances',
            'stage_field_prefix': '',
            'value_transform': copy_value,
            'targ_field': 'resourceinstanceid',
            'data_type': UUID,
            'make_tileid': False,
            'default_values': [
                ('graphid', UUID, PHYS_UUID,),
                ('graphpublicationid', UUID, 'a4ea5a7a-d7f0-11ef-a75a-0275dc2ded29',),
                ('principaluser_id', Integer, 1,),
            ], 
        },
        
    ],
}


#---------------------------------#
#- PERSON CONFIGS ----------------#
#---------------------------------#
PERSON_MODEL_UUID = 'e1d0ea1a-d770-11ef-8c40-0275dc2ded29'
PERSON_MODEL_NAME = 'person'
IMPORT_RAW_PERSON_CSV = os.path.join(DATA_DIR, 'gci-all-persons.csv')

FULLNAME_TYPE_VALUE_UUID = '828a2e14-8976-4d99-96d0-aeb1bd4223cc'

PERSON_NAME_TILE_DATA = {
    "e1d1d63c-d770-11ef-8c40-0275dc2ded29": [FULLNAME_TYPE_VALUE_UUID,], # type
    "e1d1d7ea-d770-11ef-8c40-0275dc2ded29": None, # source
    "e1d1cc64-d770-11ef-8c40-0275dc2ded29": None, # _label
    "e1d1a70c-d770-11ef-8c40-0275dc2ded29": None, # part
    "e1d1cb88-d770-11ef-8c40-0275dc2ded29": [ENG_VALUE_UUID,], # language
    "e1d1ddda-d770-11ef-8c40-0275dc2ded29": TILE_DATA_COPY_FLAG,
}

PERSON_MAPPING_CONFIGS = {
    'model_id': PERSON_MODEL_UUID,
    'staging_table': PERSON_MODEL_NAME,
    'model_staging_schema': PERSON_MODEL_NAME,
    'raw_pk_col': 'person_uuid',
    'load_path': IMPORT_RAW_PERSON_CSV,
    'mappings': [
        {
            'raw_col': 'person_uuid',
            'targ_table': 'instances',
            'stage_field_prefix': '',
            'value_transform': copy_value,
            'targ_field': 'resourceinstanceid',
            'data_type': UUID,
            'make_tileid': False,
            'default_values': [
                ('graphid', UUID, PERSON_MODEL_UUID,),
                ('graphpublicationid', UUID, '3fd6e10e-d8c6-11ef-9ef7-0275dc2ded29',),
                ('principaluser_id', Integer, 1,),
            ], 
        },
        {
            'raw_col': 'person_name',
            'targ_table': 'name',
            'stage_field_prefix': 'person_name_',
            'value_transform': make_lang_dict_value,
            'targ_field': 'name_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('name_type', ARRAY(UUID), [FULLNAME_TYPE_VALUE_UUID],),
                ('name_language', ARRAY(UUID), [ENG_VALUE_UUID],),
                ('nodegroupid', UUID, 'e1d0f244-d770-11ef-8c40-0275dc2ded29',),
            ],
            'tile_data': PERSON_NAME_TILE_DATA, 
        },
        
    ],
}



#---------------------------------#
#- SET CONFIGS -------------------#
#---------------------------------#
SET_MODEL_UUID = 'da0ed58e-d771-11ef-af99-0275dc2ded29'
SET_MODEL_NAME = 'collection_or_set'
IMPORT_RAW_SET_CSV = os.path.join(DATA_DIR, 'gci-all-sets.csv')

GCI_REF_COL_SET_UUID = 'e6d28c12-9efa-4d22-8ac9-acdb8a4f6087'

SET_DATA = [
    {
        'set_uuid': GCI_REF_COL_SET_UUID, 
        'set_name': 'Getty Conservation Institute (GCI) Reference Collection',
    },
]

SET_NAME_TILE_DATA = {
    "da0f4e7e-d771-11ef-af99-0275dc2ded29": [PREFERRED_TERM_TYPE_UUID,], # type
    "da0f3f24-d771-11ef-af99-0275dc2ded29": None, # source
    "da0f311e-d771-11ef-af99-0275dc2ded29": None, # _label
    "da0f3740-d771-11ef-af99-0275dc2ded29": [ENG_VALUE_UUID,], # language
    "da0f5676-d771-11ef-af99-0275dc2ded29": TILE_DATA_COPY_FLAG,
}

SET_MAPPING_CONFIGS = {
    'model_id': SET_MODEL_UUID,
    'staging_table': SET_MODEL_NAME,
    'model_staging_schema': SET_MODEL_NAME,
    'raw_pk_col': 'set_uuid',
    'load_path': IMPORT_RAW_SET_CSV,
    'mappings': [
        {
            'raw_col': 'set_uuid',
            'targ_table': 'instances',
            'stage_field_prefix': '',
            'value_transform': copy_value,
            'targ_field': 'resourceinstanceid',
            'data_type': UUID,
            'make_tileid': False,
            'default_values': [
                ('graphid', UUID, SET_MODEL_UUID,),
                ('graphpublicationid', UUID, '3fd6e10e-d8c6-11ef-9ef7-0275dc2ded29',),
                ('principaluser_id', Integer, 1,),
            ], 
        },
        {
            'raw_col': 'set_name',
            'targ_table': 'name',
            'stage_field_prefix': '',
            'value_transform': make_lang_dict_value,
            'targ_field': 'name_content',
            'data_type': JSONB,
            'make_tileid': True,
            'default_values': [
                ('name_type', ARRAY(UUID), [PREFERRED_TERM_TYPE_UUID],),
                ('name_language', ARRAY(UUID), [ENG_VALUE_UUID],),
                ('nodegroupid', UUID, 'da0ef9d8-d771-11ef-af99-0275dc2ded29',),
            ],
            'tile_data':SET_NAME_TILE_DATA, 
        },
        
    ],
}






ALL_MAPPING_CONFIGS = [
    # Create resource instances for different models
    
]




ARCHES_REL_VIEW_PREP_SQLS = [
    f"""
    SELECT __arches_create_resource_model_views('{PHYS_UUID}');
    """,
    
    f"""
    SELECT __arches_create_resource_model_views('{PERSON_MODEL_UUID}');
    """,
    f"""
    SELECT __arches_create_resource_model_views('{SET_MODEL_UUID}');
    """,
]
