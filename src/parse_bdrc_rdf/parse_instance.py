from rdflib import Graph, Namespace
from utils import get_id, get_ttl, get_label


BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")


def get_instance_ids(g, work_id):
    scan_ids = []
    instance_ids = []
    instances = list(g.objects(BDR[work_id], BDO["workHasInstance"]))
    for instance in instances:
        id = get_id(str(instance))
        if id[0] == "M":
            instance_ids.append(id)
        else:
            scan_ids.append(id)
    for scan_id in scan_ids:
        if f"M{scan_id}" in instance_ids:
            continue
        else:
            instance_ids.append(scan_id)
    return instance_ids 


def parse_instance_ttl(instance_id, work_id):
    instance_info = {}
    ttl_file = get_ttl(instance_id)
    g = Graph()
    try:
        g.parse(data=ttl_file, format="ttl")
    except Exception as e:
        print("cant read ttl", instance_id, e)
        return None
    title = get_label(g, instance_id)
    instance_info = {
        "@id": instance_id,
        "@type": "member",
        "Title": title,
        "Collectioin": f"/api/dts/collection/?id={work_id}"
    }
    return instance_info
