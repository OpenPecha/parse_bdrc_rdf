import requests
from rdflib import Graph, Namespace
from rdflib.namespace import SKOS, OWL, Namespace, NamespaceManager, XSD

BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")

def get_ttl(work_id):
    try:
        ttl = requests.get(f"https://ldspdi.bdrc.io/resource/{work_id}.ttl")
        return ttl.text
    except Exception as e:
        print(" TTL not Found!!!", e)
        return None

def get_id(URI):
    if URI == "None":
        return None
    return URI.split("/")[-1]

def get_label(g, work_id):
    prefLabel = str(list(g.objects(BDR[work_id], SKOS.prefLabel))[0])
    # altLabel = str(list(g.objects(BDR[work_id], SKOS.altLabel))[0])
    return prefLabel