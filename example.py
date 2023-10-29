from daikin_altherma import DaikinAltherma
d = DaikinAltherma('192.168.11.100')

d.print_all_status()

1/0  # XXX the following will erase your schedules

_present_day_schedule = {
    '0000': 17,
    '0200': 22,  # Pre-heat the house because of low-tariff
    '0640': 21,  # Back to high-tariff
    '1400': 22,  # low-tariff again
    '1640': 18,  # high-tariff
    '2000': 17,  # Shut off heating
}

_away_day_schedule = {
    '0000': 17,
    '0200': 22,  # Pre-heat the house because of low-tariff
    '0640': 20,  # Back to high-tariff
    '1400': 22,  # low-tariff again
    '1640': 18,  # high-tariff
    '2000': 17,  # Shut off heating
}

schedule = {
    'Mo': _away_day_schedule,
    'Tu': _away_day_schedule,
    'We': _present_day_schedule,
    'Th': _present_day_schedule,
    'Fr': _present_day_schedule,
    'Sa': _present_day_schedule,
    'Su': _present_day_schedule,
}
d.set_heating_schedule(schedule)

