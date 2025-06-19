import os
import pandas as pd
import uuid as GenUUID

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import RDFS, SKOS, DCTERMS


from arches_afs import general_configs
from arches_afs import utilities


"""
# testing

from arches_afs import general_configs
from arches_afs import concepts


"""



def get_concept_values_by_uri(
    concept_uri,
    db_url=general_configs.ARCHES_DB_URL
):
    """Get a conceptid, concept_uri, and preflabel
    and various valueids by a concept_uri."""
    engine = utilities.create_engine(db_url)
    sql = f"""
    SELECT
        vi.conceptid,
        vi.valueid AS concept_uri_valueid, 
        vi.value AS concept_uri, 
        vpf.valueid AS preflabel_valueid,
        vpf.value AS preflabel
    FROM public.values AS vi
    LEFT JOIN public.values AS vpf ON (
        vi.conceptid = vpf.conceptid
        AND vpf.valuetype = 'prefLabel'
    )
    WHERE vi.value = '{concept_uri}'
    AND vi.valuetype = 'identifier'
    LIMIT 1;
    """
    df = pd.read_sql(sql, engine)
    d_list = df.to_dict(orient='records')
    if len(d_list) == 0:
        return None
    return d_list[0]



def get_concept_values_by_preflabel(
    pref_label,
    db_url=general_configs.ARCHES_DB_URL
):
    """Get a conceptid, concept_uri, and preflabel
    and various valueids by a preflabel."""
    engine = utilities.create_engine(db_url)
    pref_label = str(pref_label).strip()
    pref_label = pref_label.replace("'", "''")
    sql = f"""
    SELECT
        vpf.conceptid,
        vi.valueid AS concept_uri_valueid, 
        vi.value AS concept_uri, 
        vpf.valueid AS preflabel_valueid,
        vpf.value AS preflabel
    FROM public.values AS vpf
    LEFT JOIN public.values AS vi ON (
        vi.conceptid = vpf.conceptid
        AND vpf.valuetype = 'identifier'
    )
    WHERE vpf.value = '{pref_label}'
    AND vpf.valuetype = 'prefLabel'
    LIMIT 1;
    """
    df = pd.read_sql(sql, engine)
    d_list = df.to_dict(orient='records')
    if len(d_list) == 0:
        return None
    return d_list[0]


def get_all_configs_concept_prelabel_value_ids():
    """Gets a list of all of the preflabel valueids from the mapping configs."""
    check_ids = [
        general_configs.ENG_VALUE_UUID,
        general_configs.PREFERRED_TERM_TYPE_UUID,
        general_configs.ALT_NAME_TYPE_UUID,
        general_configs.RSCI_FACET_METATYPE_UUID,
        general_configs.RSCI_FACET_TYPE_UUID,
    ]
    check_ids += general_configs.PLACE_STATEMENT_TYPE_UUIDS
    check_ids += [
        general_configs.FULLNAME_TYPE_VALUE_UUID,
    ]
    check_ids += general_configs.RSCI_NOTES_STATEMENT_TYPE_IDS 
    check_ids += general_configs.RSCI_PHYS_FORM_STATEMENT_TYPE_IDS
    check_ids += [
        general_configs.PROV_ACT_EVENT_TYPE_TRANSFERED_VALUE_UUID,
    ]
    check_ids += general_configs.RSCI_PLACE_PRODUCTION_STATEMENT_TYPE_IDS
    check_ids += general_configs.RSCI_MATERIAL_CHEM_NAME_TYPES
    check_ids += general_configs.RSCI_GBIF_NAME_TYPES
    check_ids += general_configs.RSCI_PART_STATEMENT_TYPES
    check_ids += [
        general_configs.RSCI_PART_DIMENSION_TYPE,
        general_configs.RSCI_PART_GRAMS_VALUE_UUID,
        general_configs.RSCI_PART_TYPE_VALUE_UUID,
    ]
    # Add value_ids from the mapping configs
    for config in general_configs.ALL_MAPPING_CONFIGS:
        for field, dtype, vals in config.get('default_values', []):
            skip = True
            for check in ['_type', '_language', '_unit']:
                if check in field:
                    skip = False
            if skip:
                continue
            if not isinstance(vals, list):
                vals = [vals]
            for val in vals:
                if not val in check_ids:
                    check_ids.append(val)
    return check_ids


def validate_prelabel_value_id(value_id, db_url=general_configs.ARCHES_DB_URL):
    """Check if a value id exists in the database."""
    engine = utilities.create_engine(db_url)
    sql = f"""
    SELECT
        vpf.conceptid,
        vi.valueid AS concept_uri_valueid, 
        vi.value AS concept_uri, 
        vpf.valueid AS preflabel_valueid,
        vpf.value AS preflabel
    FROM public.values AS vpf
    LEFT JOIN public.values AS vi ON (
        vi.conceptid = vpf.conceptid
        AND vpf.valuetype = 'identifier'
    )
    WHERE vpf.valueid = '{value_id}'
    AND vpf.valuetype = 'prefLabel'
    LIMIT 1;
    """
    df = pd.read_sql(sql, engine)
    d_list = df.to_dict(orient='records')
    if len(d_list) == 0:
        return None
    return d_list[0]


def validate_all_configs_concept_prelabel_value_ids():
    check_ids = get_all_configs_concept_prelabel_value_ids()
    for value_id in check_ids:
        result = validate_prelabel_value_id(value_id)
        if not result:
            print('-' * 80)
            print(f"Value id {value_id} does not exist in the database.")
            print('-' * 80)
            continue
        print(f"Value id {value_id} exists in the database.")
        print(str(result))
