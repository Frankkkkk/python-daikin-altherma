# python-daikin-altherma
talks to daikin altherma via LAN adapter BRP069A61 or BRP069A62

# How to use
## How to install ?
Simply type `pip3 install python-daikin-altherma`

## How to run
```python3
>>> from daikin_altherma import DaikinAltherma
>>> d = DaikinAltherma('192.168.10.126')
>>> print(f'My outdoor temperature is {d.outdoor_temperature}°C')
My outdoor temperature is 2.0°C
```

# Documentation
```
    class DaikinAltherma(builtins.object)
     |  DaikinAltherma(adapter_ip: str)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, adapter_ip: str)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  set_heating(self, heating_active: bool)
     |      Whether to turn the heating on(True) or off(False).
     |      You can confirm that it works by calling self.power_state
     |  
     |  set_setpoint_temperature(self, setpoint_temperature_c: float)
     |      Sets the heating setpoint (target) temperature, in °C
     |  
     |  set_tank_heating(self, powerful_active: bool)
     |      Whether to turn the water tank heating on(True) or off(False).
     |      You can confirm that it works by calling self.tank_powerful_state
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties defined here:
     |  
     |  adapter_model
     |      Returns the model of the LAN adapter
     |  
     |  indoor_setpoint_temperature
     |      Returns the indoor setpoint (target) temperature, in °C
     |  
     |  indoor_temperature
     |      Returns the indoor temperature, in °C
     |  
     |  leaving_water_temperature
     |      Returns the heating leaving water temperature, in °C
     |  
     |  outdoor_temperature
     |      Returns the outdoor temperature, in °C
     |  
     |  power_consumption
     |      Returns the energy consumption in kWh per [D]ay, [W]eek, [M]onth
     |  
     |  power_state
     |      Returns the power state
     |  
     |  tank_power_state
     |      Returns the tank power state
     |  
     |  tank_powerful_state
     |      Returns the tank powerful state
     |  
     |  tank_temperature
     |      Returns the hot water tank temperature, in °C
     |  
```

# Acknowledgments
Many thanks to [william-sy](https://github.com/william-sy/Daikin-BRP069A62) and [KarstenB](https://github.com/KarstenB/DaikinAltherma) for their bootstrap !

# Alternatives

- C# implementation: https://github.com/jbinko/dotnet-daikin-altherma
- Home assistant component: https://github.com/tadasdanielius/daikin_altherma
- ESP32 implementation: https://github.com/raomin/ESPAltherma
