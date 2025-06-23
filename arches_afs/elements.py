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
from arches_afs import elements
df_done = elements.prepare_save_elements_data()


"""

def prep_elements_data(df, df_el):
    """Prepare elements data by making lists of elements present."""
    element_cols = [c for c in df.columns.tolist() if len(c) <= 2]
    data_rows = []
    for i, row in df.iterrows():
        act_row = {
            'item_uuid': row['item_uuid'],
            'Item Label': row['Item Label'],
            'elements': [],
        }
        for col in element_cols:
            has_element = ~df[col].isnull()
            if df[has_element].empty:
                continue
            el_index = df_el['symbol'] == col
            valueid = df_el.loc[el_index, 'preflabel_valueid'].values[0]
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
):
    if df is None:
        df = pd.read_csv(raw_path)
    df_el = pd.read_csv(elements_path)
    df_done = prep_elements_data(df, df_el)
    df_done.to_csv(save_path, index=False)
    return df_done
