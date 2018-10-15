import json
from datetime import datetime
import sys
sys.path.append('../')
from src.clustering import Clustering


def cluster_entity(entity_json, cluster_json, output):
    start_time = datetime.now()
    print('start', start_time)
    clustering = Clustering(entity_json, cluster_json)
    print('start assign el', datetime.now())
    clustering.assign_chained_elink()
    print('start assign others', datetime.now())
    clustering.assign_no_where_to_go()
    print('start dump to file', datetime.now())
    with open(output, 'w') as f:
        f.write(clustering.dump_ta2_cluster(attr=True))
    print('done', datetime.now())
    print('time used', datetime.now() - start_time)


prefix = "/Users/dongyuli/isi/jsonhead/1003r4nl/"
ent = json.load(open(prefix + 'entity.json'))
clu = json.load(open(prefix + 'cluster.json'))
out = './test_real_data.txt'
cluster_entity(ent, clu, out)