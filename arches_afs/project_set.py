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
