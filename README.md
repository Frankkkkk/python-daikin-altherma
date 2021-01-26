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


# Acknowledgments
Many thanks to [william-sy](https://github.com/william-sy/Daikin-BRP069A62) and [KarstenB](https://github.com/KarstenB/DaikinAltherma) for their bootstrap !
