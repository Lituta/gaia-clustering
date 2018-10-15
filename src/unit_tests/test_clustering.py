import unittest
import sys
sys.path.append('../')
from src.clustering import Clustering


class TestExternalLinkCluster(unittest.TestCase):
    def test_elink_cluster(self):
        ent_json = {
            'sample_ent_1': ['ent_1_name', 'Organization', 'LDCxxx: m.link111'],
            'sample_ent_2': ['ent_2_name', 'Person', 'LDCxxx: m.link222'],
            'sample_ent_3': ['ent_3_name', 'Person', 'LDCxxx: m.link222'],
            'sample_ent_4': ['ent_4_name', 'Person', 'LDCxxx: NIL.xxx'],
            'sample_ent_5': ['ent_5_name', 'Person', 'LDCxxx: NIL.xxx'],
            'sample_ent_6': ['ent_6_name', 'Organization', 'LDCxxx: NIL.sadsa'],
            'sample_ent_7': ['ent_7_name', 'Organization', 'LDCxxx: NIL.asdsaf'],
            'sample_ent_8': ['ent_8_name', 'Organization', 'LDCxxx: NIL.faas']
        }

        clu_json = {
            'sample_clu_1': [['sample_ent_6'], ['sample_ent_1']],
            'sample_clu_2': [['sample_ent_2', 'sample_ent_4'], ['fake1']],
            'sample_clu_3': [['sample_ent_3', 'sample_ent_5'], ['fake2']],
            'sample_clu_4': [['sample_ent_5', 'sample_ent_7'], []],
            'sample_clu_5': [['sample_ent_8'], ['sample_ent_8']]
        }
        expected = '''LDCxxx: m.link111
sample_ent_1
sample_ent_6
LDCxxx: m.link222
sample_ent_2
sample_ent_3
sample_ent_4
sample_ent_5
sample_ent_7'''
        clustering = Clustering(ent_json, clu_json)
        clustering.assign_chained_elink()
        res = clustering.dump_ta2_cluster()
        self.assertEqual(res, expected)

    def test_all_cluster(self):
        # TODO: test clustering.assign_no_where_to_go
        ent_json = {
            'sample_ent_1': ['similar_name_1', 'Organization', 'LDCxxx: m.link111'],
            'sample_ent_2': ['ent_2_name', 'Person', 'LDCxxx: m.link222'],
            'sample_ent_3': ['ent_3_name', 'Person', 'LDCxxx: m.link222'],
            'sample_ent_4': ['ent_4_name', 'Person', 'LDCxxx: NIL.xxx'],
            'sample_ent_5': ['ent_5_name', 'Person', 'LDCxxx: NIL.xxx'],
            'sample_ent_6': ['similar_name_6', 'Organization', 'LDCxxx: NIL.sadsa'],
            'sample_ent_7': ['ent_7_name', 'Organization', 'LDCxxx: NIL.asdsaf'],
            'sample_ent_8': ['ent_8_name', 'Organization', 'LDCxxx: NIL.faas'],
            'sample_ent_9': ['similar_name_x', 'Organization', 'LDCxxx: NIL.faas'],
            'sample_ent_10': ['similar_name_y', 'Organization', 'LDCxxx: NIL.faas'],
            'sample_ent_11': ['not_sim_1', 'Organization', 'LDCxxx: NIL.faas'],
            'sample_ent_12': ['not_sim_2', 'Organization', 'LDCxxx: NIL.faas']

        }

        clu_json = {
            'sample_clu_1': [['sample_ent_6'], ['sample_ent_1']],
            'sample_clu_2': [['sample_ent_2', 'sample_ent_4'], ['fake1']],
            'sample_clu_3': [['sample_ent_3', 'sample_ent_5'], ['fake2']],
            'sample_clu_4': [['sample_ent_5', 'sample_ent_7'], []],
            'sample_clu_5': [['sample_ent_8'], ['sample_ent_8']],
            'sample_clu_6': [['sample_ent_9'], ['sample_ent_10']],
            'sample_clu_7': [['sample_ent_11'], ['sample_ent_11']],
            'sample_clu_8': [['sample_ent_12'], ['sample_ent_12']]
        }
        expected = '''LDCxxx: m.link111
sample_ent_1
sample_ent_6
sample_ent_9
sample_ent_10
LDCxxx: m.link222
sample_ent_2
sample_ent_3
sample_ent_4
sample_ent_5
sample_ent_7
sample_ent_8
NO_EXTERNAL_LINK_CLUSTERS_0
sample_ent_11
sample_ent_12'''
        clustering = Clustering(ent_json, clu_json)
        clustering.assign_chained_elink()
        clustering.assign_no_where_to_go()
        res = clustering.dump_ta2_cluster()
        self.assertEqual(res, expected)
        pass


