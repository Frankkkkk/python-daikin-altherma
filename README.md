# python-daikin-altherma

talks to daikin altherma via LAN adapter BRP069A61 or BRP069A62

# How to use

## How to install ?

Simply get it from [pypi](https://pypi.org/project/python-daikin-altherma/) by:
`pip3 install python-daikin-altherma`

## How to run

```python3
>>> from daikin_altherma import DaikinAltherma
>>> d = DaikinAltherma('192.168.10.126')
>>> print(f'My outdoor temperature is {d.outdoor_temperature}°C')
My outdoor temperature is 2.0°C
>>> d.print_all_status()
Daikin adapter: 192.168.11.100 BRP069A61
Daikin unit: EAVH16S23DA6V 0
Daikin time: 2023-10-20 18:56:08
Hot water tank:
    Current: 48.0°C (target 49.0°C)
    Heating enabled: True (Powerful: False)
Heating:
    Outdoor temp:14.0°C
    Indoor temp: 21.5°C
    Heating target: 24.0°C (is heating enabled: True)
    Leaving water: 29.0°C
    Heating mode: heating
    Schedule: {'Mo': {'0000': 18.0, '0600': 20.0, '1200': 22.0, '1500': 20.0, '1800': 18.0}, 'Tu': {'0000': 18.0, '0600': 20.0, '1800': 18.0}, 'We': {'0000': 18.0, '0600': 20.0, '1800': 18.0}, 'Th': {'0000': 18.0, '0600': 20.0, '1200': 22.0, '1500': 20.0, '1800': 18.0}, 'Fr': {'0000': 18.0, '0600': 20.0, '1200': 22.0, '1500': 20.0, '1800': 18.0}, 'Sa': {'0000': 18.0, '0600': 20.0, '1200': 22.0, '1500': 20.0, '1800': 18.0}, 'Su': {'0000': 18.0, '0600': 20.0, '1200': 22.0, '1500': 20.0, '1800': 18.0}}

```

## Schedules

You can set schedules using `set_heating_schedule(schedule)`. Your best bet is to
look at the [example file](example.py).

# Documentation

```text
    class DaikinAltherma(builtins.object)
     |  DaikinAltherma(adapter_ip: str)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, adapter_ip: str)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  print_all_status(self)
     |  
     |  set_heating_enabled(self, heating_active: bool)
     |      Whether to turn the heating on(True) or off(False).
     |      You can confirm that it works by calling self.is_heating_enabled
     |  
     |  set_heating_schedule(self, schedule: dict[str, dict[str, float]])
     |      Sets the heating schedule for the heating.
     |  
     |  set_holiday_mode(self, on_holiday: bool)
     |      Whether to turn the holiday mode on(True) or off(False).
     |      You can confirm that it works by calling self.is_holiday_mode
     |  
     |  set_setpoint_temperature(self, setpoint_temperature_c: float)
     |      Sets the heating setpoint (target) temperature, in °C
     |
     |  set_leaving_water_temperature_offset(self, offset_temperature_c: int)
     |      Sets the heating leaving water offset temperature, in °C
     |  
     |  set_tank_heating_enabled(self, powerful_active: bool)
     |      Whether to turn the water tank heating on(True) or off(False).
     |      You can confirm that it works by calling self.is_tank_heating_enabled
     |  
     |  set_unit_datetime(self, d)
     |      Sets the datetime of your unit. Does not work on all units. See `is_unit_datetime_adjustable`
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties/methods defined here:
     |      All properties will return None if not supported.
     |  
     |  adapter_model
     |      Returns the model of the LAN adapter.
     |      Ex: BRP069A61
     |
     |  available_services(unit_nr)
     |      Returns a JSON with capacities for each unit. unit_nr is in range [0..2] normally
     |  
     |  control_mode
     |      Returns the type of control used for heating. This is an installation setting, and controls for example the availability of indoor_temperature 
     |
     |  heating_mode
     |      Returns whether the heat pump is heating or cooling.
     |  
     |  heating_schedule
     |      Returns the HeatingSchedule list heating
     |  
     |  heating_schedule_state
     |      Returns the actual heating schedule state
     |  
     |  indoor_setpoint_temperature
     |      Returns the indoor setpoint (target) temperature, in °C
     |  
     |  indoor_temperature
     |      Returns the indoor temperature, in °C
     |  
     |  indoor_unit_software_version
     |      Returns the unit software version
     |  
     |  indoor_unit_version
     |      Returns the unit version
     |  
     |  is_heating_enabled
     |      Returns if the unit heating is enabled
     |
     |  is_heating_[warning|error|emergency]
     |      Returns if heating has a warning or an error or an emergency
     |
     |  heating_error_status
     |      Returns the heating status: "OK" or "Warning" or "Error" or "Emergency"     
     |  
     |  is_holiday_mode
     |      Returns if the holiday mode active or not
     |  
     |  is_tank_heating_enabled
     |      Returns if the tank heating is currently enabled
     |
     |  is_tank_[warning|error|emergency]
     |      Returns if tank heating has a warning or an error or an emergency
     |
     |  tank_error_status
     |      Returns the tank status: "OK" or "Warning" or "Error" or "Emergency"
     |  
     |  is_tank_powerful
     |      Returns if the tank is in powerful state
     |
     |  is_unit_datetime_adjustable
     |      Returns True if the datetime of your unit is adjustable
     |  
     |  leaving_water_temperature
     |      Returns the heating leaving water temperature, in °C
     |  
     |  leaving_water_temperature_offset
     |      Returns the heating leaving water offset temperature, in °C
     |  
     |  outdoor_temperature
     |      Returns the outdoor temperature, in °C
     |  
     |  outdoor_unit_software_version
     |      Returns the unit software version
     |  
     |  pin_code
     |      Returns the pin code of the LAN adapter
     |  
     |  power_consumption
     |      Returns the heating energy consumption in kWh per [D]ay, [W]eek, [M]onth
     |  
     |  remote_setting_version
     |      Returns the remote console setting version
     |  
     |  remote_software_version
     |      Returns the remote console setting software version
     |  
     |  tank_schedule
     |      Returns the TankSchedule list heating
     |  
     |  tank_schedule_state
     |      Returns the actual tank schedule state
     |  
     |  tank_setpoint_temperature
     |      Returns the hot water tank setpoint (target) temperature, in °C
     |  
     |  tank_temperature
     |      Returns the hot water tank temperature, in °C
     |
     |  tank_power_consumption
     |      Returns the tank energy consumption in kWh per [D]ay, [W]eek, [M]onth
     |  
     |  unit_datetime
     |      Returns the current date of the unit. Is refreshed every minute or so
     |  
     |  unit_model
     |      Returns the model of the heating unit.
     |      Ex: EAVH16S23DA6V
     |  
     |  unit_type
     |      Returns the type of unit
     | 
     |  in_installerstate and tank_in_installerstate
     |      Returns if the heating is in the installer mode, will have limited functionality in that case
     |
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  DATETIME_FMT = '%Y%m%dT%H%M%SZ'
     |  
     |  DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
     |  
     |  UserAgent = 'python-daikin-altherma'
```

# Acknowledgments

Many thanks to [william-sy](https://github.com/william-sy/Daikin-BRP069A62) and [KarstenB](https://github.com/KarstenB/DaikinAltherma) for their bootstrap !

# Alternatives

- C# implementation: https://github.com/jbinko/dotnet-daikin-altherma
- Home assistant component: https://github.com/tadasdanielius/daikin_altherma
- ESP32 implementation: https://github.com/raomin/ESPAltherma
