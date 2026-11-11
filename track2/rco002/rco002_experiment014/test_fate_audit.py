#!/usr/bin/env python3
import unittest
from fate_audit import successor_candidates

class FakeSim:
    @staticmethod
    def profile_similarity(a,b):
        return 1.0 if a==b else 0.0

class FateAuditTests(unittest.TestCase):
    def test_successor_with_particle_bridge(self):
        old={"target_group":{"sites":[1,2],"particle_ids":[7,8],"profile":{"AA>A":1}}}
        new={"groups":[
            {"fid":72,"sites":[3,4],"particle_ids":[7,9],"size":2,"profile":{"AA>A":1}},
            {"fid":88,"sites":[9,10],"particle_ids":[20,21],"size":2,"profile":{}}
        ]}
        result=successor_candidates(FakeSim,old,new)
        self.assertEqual(result[0]["new_fid"],72)
        self.assertEqual(result[0]["particle_overlap"],1)

    def test_no_prior_target(self):
        self.assertEqual(successor_candidates(FakeSim,{"target_group":None},{"groups":[]}),[])

if __name__=="__main__":
    unittest.main()
