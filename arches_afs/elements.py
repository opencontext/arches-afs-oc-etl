import json
import os
import pandas as pd
import uuid as GenUUID

from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import RDFS, SKOS, DCTERMS


from arches_afs import general_configs
from arches_afs import concepts
from arches_afs import utilities


"""
# testing

from arches_afs import general_configs
from arches_afs import elements
df_done = elements.prepare_save_elements_data()


"""


def update_citation_to_html(
    cite_path=general_configs.ELEMENTS_CITE_CSV,
):
    """A quick and dirty HTML update"""
    imp_path = os.path.join(general_configs.DATA_DIR, 'phys_elements.csv')
    df = pd.read_csv(imp_path)
    df_cite = pd.read_csv(cite_path)
    for i, row in df.iterrows():
        uuid = row['resourceinstanceid']
        tileid = row['mat_tileid']
        cite_index = df_cite['item_uuid'] == uuid
        cite_html = df_cite[cite_index]['statement_cite_html'].iloc[0]
        cite_dict = general_configs.make_lang_dict_value(cite_html)
        cite_json = json.dumps(cite_dict, ensure_ascii=False)
        df.at[i, 'mat_material_data_assignment_statement_content'] = cite_json
    df.to_csv(imp_path, index=False)



def prep_elements_data(df, df_el, df_cite):
    """Prepare elements data by making lists of elements present."""
    element_cols = [c for c in df.columns.tolist() if len(c) <= 2]
    data_rows = []
    valid_valueids = []
    for i, row in df.iterrows():
        uuid = row['item_uuid']
        cite_index = df_cite['item_uuid'] == uuid
        statement_cite = df_cite[cite_index]['statement_cite_html'].iloc[0]
        act_row = {
            'item_uuid': uuid,
            'Item Label': row['Item Label'],
            'statement_cite': statement_cite,
            'elements': [],
        }
        for col in element_cols:
            has_element = ~df[col].isnull()
            if df[has_element].empty:
                continue
            el_index = df_el['symbol'] == col
            valueid = df_el.loc[el_index, 'preflabel_valueid'].values[0]
            if valueid not in valid_valueids:
                valid = concepts.validate_prelabel_value_id(valueid)
                if not valid:
                    raise ValueError(
                        f'No element {col} valueid: {valueid} in the db'
                    )
                valid_valueids.append(valueid)
            act_row['elements'].append(valueid)
        data_rows.append(act_row)
    df_done = pd.DataFrame(data_rows)
    df_done['elements'] = df_done['elements'].apply(lambda x: json.dumps(x))
    return df_done


def prepare_save_elements_data(
    df=None, 
    raw_path=general_configs.RAW_IMPORT_CSV, 
    save_path=general_configs.IMPORT_ELEMENTS_CSV,
    elements_path=general_configs.ELEMENTS_CSV,
    cite_path=general_configs.ELEMENTS_CITE_CSV,
):
    if df is None:
        df = pd.read_csv(raw_path)
    df_el = pd.read_csv(elements_path)
    df_cite = pd.read_csv(cite_path)
    df_done = prep_elements_data(df, df_el, df_cite)
    df_done.to_csv(save_path, index=False)
    return df_done
