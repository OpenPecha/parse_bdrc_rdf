import requests
from collections import defaultdict

from pyewts import pyewts
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, Namespace, NamespaceManager, RDF, SKOS, XSD

BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")

SUPPORTED_LANGS = {"bo", "zh", "en", "sa"}
LANGUAGE_ALIASES = {
    "bo": "bo",
    "bo-x-ewts": "bo",
    "zh": "zh",
    "zh-Hans": "zh",
    "en": "en",
    "sa": "sa",
    "sa-x-ewts": "sa",
    "sa-x-iast": "sa",
}
MAIN_AUTHOR_ROLE_IDS = {"R0ER0019"}
EWTS_CONVERTER = pyewts()

def get_ttl(work_id):
    try:
        ttl = requests.get(f"https://ldspdi.bdrc.io/resource/{work_id}.ttl")
        return ttl.text
    except Exception as exc:
        print(" TTL not Found!!!", exc)
        return None

def get_id(uri):
    if uri == "None":
        return None
    return uri.split("/")[-1]

def get_label(g, work_id):
    pref_label = str(list(g.objects(BDR[work_id], SKOS.prefLabel))[0])
    return pref_label

def _normalize_language_tag(lang):
    if lang is None:
        return None
    if lang in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[lang]
    base = lang.split("-")[0]
    if base in SUPPORTED_LANGS:
        return base
    return None

def _get_resource_graph(resource_id):
    ttl_data = get_ttl(resource_id)
    if not ttl_data:
        return None
    resource_graph = Graph()
    try:
        resource_graph.parse(data=ttl_data, format="ttl")
    except Exception as exc:
        print("cant read ttl", resource_id, exc)
        return None
    return resource_graph

def _is_main_author(g, creator):
    role_uri = g.value(creator, BDO.role)
    if role_uri is None:
        return False
    role_id = get_id(str(role_uri))
    return role_id in MAIN_AUTHOR_ROLE_IDS

def _get_agent_uri(g, creator):
    agent_uri = g.value(creator, BDO.agent)
    if agent_uri is None:
        return None
    return agent_uri

def _iter_main_author_agents(g, work_id):
    for creator in g.objects(BDR[work_id], BDO.creator):
        if not _is_main_author(g, creator):
            continue
        agent_uri = _get_agent_uri(g, creator)
        if agent_uri is None:
            continue
        agent_id = get_id(str(agent_uri))
        if agent_id is None:
            continue
        agent_graph = _get_resource_graph(agent_id)
        if agent_graph is None:
            continue
        yield agent_graph, agent_uri

def get_author(g, work_id):
    author_names = defaultdict(set)
    for agent_graph, agent_uri in _iter_main_author_agents(g, work_id):
        for label_literal in agent_graph.objects(agent_uri, SKOS.prefLabel):
            normalized_lang = _normalize_language_tag(label_literal.language)
            if normalized_lang is None:
                continue
            label_text = str(label_literal)
            if normalized_lang == "bo":
                label_text = EWTS_CONVERTER.toUnicode(label_text)
            author_names[normalized_lang].add(label_text)
    return {lang: "; ".join(sorted(values)) for lang, values in author_names.items()}

def _get_topic_labels(topic_id):
    topic_graph = _get_resource_graph(topic_id)
    if topic_graph is None:
        return None
    topic_uri = BDR[topic_id]
    if (topic_uri, RDF.type, BDO.Topic) not in topic_graph:
        return None
    label_map = defaultdict(set)
    for label_literal in topic_graph.objects(topic_uri, SKOS.prefLabel):
        normalized_lang = _normalize_language_tag(label_literal.language)
        if normalized_lang is None:
            continue
        label_text = str(label_literal)
        if normalized_lang == "bo":
            label_text = EWTS_CONVERTER.toUnicode(label_text)
        label_map[normalized_lang].add(label_text)
    if not label_map:
        return None
    return label_map

def get_categories(g, work_id):
    aggregated_labels = defaultdict(set)
    seen_ids = set()
    for about in g.objects(BDR[work_id], BDO.workIsAbout):
        topic_id = get_id(str(about))
        if topic_id is None or topic_id in seen_ids:
            continue
        labels = _get_topic_labels(topic_id)
        if labels is None:
            continue
        for lang, values in labels.items():
            aggregated_labels[lang].update(values)
        seen_ids.add(topic_id)
    return {lang: sorted(values) for lang, values in aggregated_labels.items()}

if __name__ == "__main__":
    work_id = "WA2KG1677"
    ttl_file = get_ttl(work_id)
    g = Graph()
    g.parse(data=ttl_file, format="ttl")
    categories = get_categories(g, work_id)
    print(categories)