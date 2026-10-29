import unittest
import numpy as np
from inspect_pairing_tables import SIZES,validate
from paired_pilot_contract import verify,check_counters


class PairingTableTests(unittest.TestCase):
    def adjacent(self):
        tables=[]
        for n in SIZES:
            y,x=np.indices((n,n));tables.append(np.stack((np.where(x.ravel()%2==0,1,-1),np.zeros(n*n,dtype=int)),axis=-1))
        return np.concatenate(tables)

    def test_transform_involution_and_gaussian_negative_control(self):
        data=self.adjacent()
        self.assertEqual(len(validate(data,False)),3)
        with self.assertRaises(ValueError):validate(data)

    def test_missing_zero_out_of_range_and_reverse_link(self):
        data=self.adjacent()
        for bad in (data[:-1],np.zeros_like(data)):
            with self.assertRaises(ValueError):validate(bad,False)
        for delta in ((128,0),(2,0)):
            bad=data.copy();bad[0]=delta
            with self.assertRaises(ValueError):validate(bad,False)

    def test_effective_gaussian_requires_upload_and_policy(self):
        contract='PT_PAIRED_CONTRACT enabled=1 adjacentReciprocal=0 pairOwnedShifts=1 vectorShading=1\n'
        policy='PT_PAIR_POLICY gaussian=1 residentTables=3 activeTablesPerFrame=1 sigma=16 frameTransforms=1\n'
        upload='PT_PAIR_TABLE_UPLOAD tables=3 entries=161516 bytes=1292128 sigma=16 format=RG32_SINT\n'
        self.assertIn('Gaussian',verify(contract+policy+upload,True,True)['policy'])
        for bad in (contract,contract+policy,contract+policy+upload.replace('161516','1'),contract+policy+upload+policy.replace('activeTablesPerFrame=1','activeTablesPerFrame=3')):
            with self.assertRaises(ValueError):verify(bad,True,True)
        with self.assertRaises(ValueError):verify('',False,True)
