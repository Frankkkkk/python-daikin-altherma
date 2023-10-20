import unittest
import pprint

from daikin_altherma import DaikinAltherma


S1 = '$NULL|1|0000,180;0450,200;2300,180;,;,;,;0000,180;0450,200;2300,180;,;,;,;0000,180;0450,200;2300,180;,;,;,;0000,180;0450,200;2300,180;,;,;,;0000,180;0450,200;2300,180;,;,;,;0000,180;0450,200;2300,180;,;,;,;0000,180;0450,200;2300,180;,;,;,'


class TestSchedule(unittest.TestCase):

    def test_schedule(self):
        ''' Tests conversion from str to dict to str'''
        s_dict = DaikinAltherma._unmarshall_schedule(S1)
        s_str = DaikinAltherma._marshall_schedule(s_dict)
        assert S1 == s_str

    def test_schedule_dict(self):
        schedule = {
            'Mo': {'0000': 22.0},
            'Tu': {}, 'We': {}, 'Th': {}, 'Fr': {}, 'Sa': {}, 'Su': {},
        }
        back_schedule = DaikinAltherma._unmarshall_schedule(DaikinAltherma._marshall_schedule(schedule))
        assert schedule == back_schedule
