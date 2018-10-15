import json
from src.entity import Entity
from src.cluster import Cluster

# TODO: load mapping
OTHERS = 'others'
JARO_CACHE = {}     # {(string1, string2): distance_float} where string1 < string2


class Clustering(object):
    def __init__(self, entity_json: dict, cluster_json: dict, dbpedia2freebase='../dbpedia2freebase.json'):
        """
        init
        :param entity_json: raw info {entity_uri: [name_or_{translation:[tran1,tran2]}, type, external_link], ... }
        :param cluster_json: raw info {cluster_uri: [[member1, member2], [prototype1]], ... }
        """
        self.MAP_TO_FREEBASE = json.load(dbpedia2freebase)
        self.entities = {}              # self.entities:        {entity_uri: Entity instance}
        self.ta2_clusters = {}          # self.ta2_clusters:    {external_link: Cluster instance}
        self.no_link = {}               # self.no_link:         {entity_no_elink_uri: [(elinks), (ta1_cluster_uris)]}
        self.cluster_to_ent = {}        # self.cluster_to_ent:  {ta1_cluster_uri: set(entity_no_elink_uris)}
        self.no_where_to_go = []        # self.no_where_to_go:  [Cluster: merged no el ents ta1 clusters]

        self.init_el_based_clusters(entity_json, cluster_json)

    def init_el_based_clusters(self, entity_json, cluster_json):
        """
        create Entity instance for each entity and put in self.entities ;
        create Cluster instance for each external link and put entities with elink to corresponding ta2_clusters;
        go over ta1 clusters and put every no-elink entity to self.no_link, record siblings' elinks or ta1 cluster uri.
        :param entity_json: raw info {entity_uri: [name_or_{translation:[tran1,tran2]}, type, external_link], ... }
        :param cluster_json: raw info {cluster_uri: [[member1, member2], [prototype1]], ... }
        :return: None
        """

        # init all entities
        # init ta2 clusters, group by external links(skip 'others')
        for ent, attr in entity_json.items():
            name, _type, link = attr
            names = self.parse_name(name)
            _type = _type.rsplit('#', 1)[-1]
            link = self.parse_link(link)
            self.entities[ent] = Entity(ent, names, _type, link)
            if link != OTHERS:
                if link not in self.ta2_clusters:
                    self.ta2_clusters[link] = Cluster([])
                self.ta2_clusters[link].add_member(self.entities[ent])
            else:
                self.no_link[ent] = [set(), set()]

        '''
        now we have:
        self.entities - dict, each key is an entity uri, each value is the corresponding Entity object
        self.ta2_clusters - dict, each key is a real external link, each value is the corresponding Cluster object
        self.no_link - dict, each key is an entity uri, each value is two sets:
                one to store elinks related to the entity, the other to store the ta1 cluster uri
        then all the entities are either in ta2_clusters's Clusters, or in no_link's keys
        '''

        # process ta1 clusters
        for cluster, mems in cluster_json.items():
            self.cluster_to_ent[cluster] = set()
            cur = Cluster([])
            members, prototypes = mems
            cur_no_link = set()
            for m in members:
                cur.add_member(self.entities[m])
                if self.entities[m].link == OTHERS:
                    cur_no_link.add(m)
            for m in prototypes:
                if m in self.entities:
                    cur.add_member(self.entities[m])
                    if self.entities[m].link == OTHERS:
                        cur_no_link.add(m)
            for elink in cur.links:
                if elink == OTHERS:
                    for m in cur_no_link:
                        self.cluster_to_ent[cluster].add(m)
                        self.no_link[m][1].add(cluster)
                else:
                    for m in cur_no_link:
                        self.cluster_to_ent[cluster].add(m)
                        self.no_link[m][0].add(elink)

    def assign_chained_elink(self):
        """
        now we have filled self.no_links: {entity_uri: [(some_external_links), (some_ta1_cluster_uris)], ... }
        and self.cluster_to_ent - dict: {ta1_cluster_uri: (entities_with_no_link_uris), ... }
        :return: None
        """
        # for each entity in no_link, try to find a best place to go
        visited = set()
        total = len(self.no_link.items())
        cnt = 0
        for ent_uri, elink_ta1cluster in self.no_link.items():
            cnt += 1
            if cnt % 10000 == 0:
                print('process %d of %d' % (cnt, total))
            elinks, ta1s = elink_ta1cluster
            cur_ent = self.entities[ent_uri]
            if len(elinks):
                cur_cluster = self.get_best(cur_ent, elinks)
                cur_cluster.add_member(cur_ent)
            else:
                # not directly clustered with entity with elink:
                # no elinks, try to find chained elinks, otherwise no where to go
                if ent_uri in visited:
                    continue
                visited_no_el_sibling_ent = {ent_uri}
                elinks = set()
                added = ta1s
                to_check = list(ta1s)
                # TODO: confidence by hops? now ents with >= 1 hop sibling with elinks are treat in the same way
                while to_check:
                    cur_cluster = to_check.pop()
                    for sibling in self.cluster_to_ent[cur_cluster]:
                        if len(self.no_link[sibling][0]):
                            # find external links
                            elinks = elinks.union(self.no_link[sibling][0])
                        else:
                            visited_no_el_sibling_ent.add(ent_uri)
                        for next_hop_cluster in self.no_link[sibling][1]:
                            # add other chained clusters to check
                            if next_hop_cluster not in added:
                                added.add(next_hop_cluster)
                                to_check.append(next_hop_cluster)
                if len(elinks):
                    for covered_ent in visited_no_el_sibling_ent:
                        # TODO: chained elinks may be very different in CU clusters, should make use of confidence ?
                        cur_cluster = self.get_best(self.entities[covered_ent], elinks)
                        cur_cluster.add_member(self.entities[covered_ent])
                else:
                    cur_cluster = Cluster([self.entities[covered_ent] for covered_ent in visited_no_el_sibling_ent])
                    self.no_where_to_go.append(cur_cluster)
                visited = visited.union(visited_no_el_sibling_ent)

    def assign_no_where_to_go(self, threshold: float=0.9):
        """
        now all entities related to one or more external links have been put into a ta2 cluster,
        and the chained no-elink clusters are merged,
        compare each cluster to existing ta2 clusters to merge them,
        otherwise compare each pair of clusters in self.no_where_to_go to decide if merge them
        :return: None
        """
        print('try to assign no where to go to a elink cluster if jaro >= 0.9')
        cnt = 0
        total = len(self.no_where_to_go)
        lefts = []
        for i in range(len(self.no_where_to_go)):
            cnt += 1
            print('nowheretogo1 %d of %d' % (cnt, total))
            # try to assign to existing ta2 cluster, no chained to avoid FPs
            cur_i = self.no_where_to_go[i]
            to_go = self.get_best(target=cur_i, threshold=threshold)
            if to_go:
                for mem in cur_i.members.values():
                    to_go.add_member(mem)
            else:
                lefts.append(i)

        # no similar ta2 cluster to go, try to merge with others
        print('no similar ta2 cluster to go, try to merge with others')
        edges = {}
        for i in range(len(lefts) - 1):
            for j in range(i + 1, len(lefts)):
                cur_i = self.no_where_to_go[lefts[i]]
                cur_j = self.no_where_to_go[lefts[j]]
                if cur_i.calc_similarity(cur_j, JARO_CACHE, threshold) > threshold:
                    if i not in edges:
                        edges[i] = []
                    if j not in edges:
                        edges[j] = []
                    edges[i].append(j)
                    edges[j].append(i)

        print('no similar ta2 cluster to go, try to merge with others - BFS')
        groups = []
        visited = set()
        for i in edges:
            if i not in visited:
                to_check = [i]
                added = {i}
                idx = 0
                while idx < len(to_check):
                    cur = to_check[idx]
                    idx += 1
                    for j in edges[cur]:
                        if j not in added:
                            to_check.append(j)
                            added.add(j)
                visited = visited.union(added)
                groups.append(to_check)

        print('no similar ta2 cluster to go, try to merge with others - ASSIGNMENT')
        for i in range(len(groups)):
            cur = Cluster([])
            for _ in groups[i]:
                for mem in self.no_where_to_go[lefts[_]].members.values():
                    cur.add_member(mem)
            if cur.members:
                self.ta2_clusters['NO_EXTERNAL_LINK_CLUSTERS_%d' % i] = cur

    def get_best(self, target: Entity or Cluster, elinks: set=None, threshold: float=0) -> Cluster:
        if not elinks:
            elinks = self.ta2_clusters
        if len(elinks) == 1:
            return self.ta2_clusters[list(elinks)[0]]
        max_simi = -1
        max_el = None
        for el in elinks:
            cur_simi = self.ta2_clusters[el].calc_similarity(target, JARO_CACHE)
            if cur_simi > max_simi:
                max_simi = cur_simi
                max_el = el
        if max_simi >= threshold:
            return self.ta2_clusters[max_el]

    def dump_ta2_cluster(self, attr=False):
        res = []
        for el, cluster in self.ta2_clusters.items():
            res.append(el)
            if attr:
                details = json.dumps(cluster.groupby_attr, indent=2, ensure_ascii=False)
            else:
                details = cluster.dump_members()
            res.append(details)
        return '\n'.join(res)

    def parse_link(self, link: str):
        # http://dbpedia.org/resource/Vladimir_Potanin
        # LDC2015E42:NIL00132305
        # LDC2015E42:m.083kb
        if link.startswith('http://dbpedia'):
            return self.MAP_TO_FREEBASE.get(link, link)
        link = link.split(':', 1)[-1].strip()
        return link if link.startswith('m.') else OTHERS

    @staticmethod
    def parse_name(name: str):
        if name.startswith('{'):
            return json.loads(name).get('translation', [''])
        return [name]



"""
20181012 TODO:
1. freebase and dbpedia mapping
2. what to do with filter type ???
3. dump results
4. get name from cluster?
5. event clustering
6. relation clustering
"""

