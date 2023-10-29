import datetime
import time
from daikin_altherma import DaikinAltherma
d = DaikinAltherma('192.168.11.100')

now = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
d.set_unit_datetime(now)

while True:
    dat = d.unit_datetime
    now = datetime.datetime.utcnow()
    print(f'NOW: {now}\nDAI: {dat}')
    print(abs(datetime.datetime.utcnow() - dat))
    time.sleep(1)

#print(f'BEF: {d.unit_datetime}')
#d.set_unit_datetime(now)
#print(f'AFT: {d.unit_datetime}')
#print(d.tank_schedule_state)
#print(d.heating_schedule_state)
#print(d.tank_schedule)

#d.print_all_status()
1/0

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

