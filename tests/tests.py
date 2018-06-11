# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 18:32:47 2018

@author: pmp13wm
"""

import unittest
from poweroften import PowerOfTen

class TestStringMethods(unittest.TestCase):

    def test_search(self):
        po10 = PowerOfTen()
        df = po10.search('Will', 'Mycroft')
        self.assertTrue(7172 in df.index)
        
    def test_get_athlete(self):
        po10 = PowerOfTen()
        athlete_info, yearly_info, seasons_bests, results = po10.get_athlete(7172)
        self.assertEqual(athlete_info['Name'], 'William Mycroft')
        self.assertEqual(athlete_info['Gender'], 'Male')
        self.assertTrue('Oxford Uni' in yearly_info[2010]['clubs'])
        self.assertEqual(seasons_bests.loc['3000SC', '2017'], '9:01.89')
        self.assertEqual(results[results.MeetingId == 199052].iloc[0].Event, '3000SC')
        
    def test_get_rankings(self):
        po10 = PowerOfTen()
        df = po10.get_rankings('3000SC', 'SEN', 'M', 2017)
        self.assertEqual(df.loc[7172].Rank, 17)

    def test_get_results(self):
        po10 = PowerOfTen()
        df = po10.get_results(199052)['3000SC B']
        self.assertEqual(df[df.AthleteId == 7172].iloc[0].Perf, '9:01.89')
        
if __name__ == '__main__':
    unittest.main()
