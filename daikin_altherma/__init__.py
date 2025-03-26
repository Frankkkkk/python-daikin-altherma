import json
from typing import Callable
from dataclasses import dataclass
import enum
import logging
import uuid
import datetime

from websocket import create_connection
import dpath.util

Day = Hour = str
Temperature = float
HeatingSchedule = dict[Day, dict[Hour, Temperature]]
TankSchedule = dict[Day, dict[Hour, 'TankStateEnum']]


# XXX use StrEnum in some years when distros will have py 3.11
class TankStateEnum(str, enum.Enum):
    OFF = "off"
    COMFORT = "comfort"
    ECO = "eco"

    def __str__(self):
        return str(self.value)

    @staticmethod
    def int_to_state(x: int) -> 'TankStateEnum':
        x = str(x)
        return {
            "2": TankStateEnum.OFF,
            "1": TankStateEnum.COMFORT,
            "0": TankStateEnum.ECO,
        }[x]


class HeatingOperationMode(str, enum.Enum):
    Heating = 'Heating'
    Cooling = 'Cooling'


@dataclass
class _ScheduleState:
    OperationMode: HeatingOperationMode
    StartTime: int
    Day: str  # XXX enum


@dataclass
class HeatingScheduleState(_ScheduleState):
    TargetTemperature: float


@dataclass
class TankScheduleState(_ScheduleState):
    TankState: TankStateEnum


class DaikinAltherma:
    UserAgent = "python-daikin-altherma"
    DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    DATETIME_FMT = "%Y%m%dT%H%M%SZ"
    
    # Not implemented, but potentially interesting query paths are:
    # 1|2/UnitStatus/WeatherDependentState/la
    # 1|2/UnitStatus/TargetTemperatureOverruledState/la
    # 1|2/UnitInfo/SerialNumber/la (may return "--" if not available)
    # 1|2/UnitInfo/Manufacturer/la ("Daikin")
    # 1|2/UnitIdentifier/Icon (returns a number, like 8 or 9, for the Onecta App)
    # 1|2/UnitIdentifier/Name (returns a string, like $NULL, for the Onecta App)
        
    def _heating_value_parser(x):
        return float(x) / 10

    def __init__(self, adapter_ip: str):
        self.adapter_ip = adapter_ip
        self.ws = create_connection(f"ws://{self.adapter_ip}/mca", timeout=2)

    def _requestValue(self, item: str, output_path: str, payload=None):
        reqid = uuid.uuid4().hex[0:5]
        js_request = {
            "m2m:rqp": {
                "fr": DaikinAltherma.UserAgent,
                "rqi": reqid,
                "op": 2,
                "to": f"/[0]/{item}",
            }
        }
        if payload:
            set_value_params = {
                "ty": 4,
                "op": 1,
                "pc": {
                    "m2m:cin": payload,
                },
            }
            js_request["m2m:rqp"].update(set_value_params)

        self.ws.send(json.dumps(js_request))
        result = json.loads(self.ws.recv())

        assert result["m2m:rsp"]["rqi"] == reqid
        assert result["m2m:rsp"]["to"] == DaikinAltherma.UserAgent

        try:
            return dpath.util.get(result, output_path)
        except KeyError:
            logging.error(f"Could not get data for item {item}. Maybe the unit is starting up or relevant module is not installed?")
            return None

    def _requestValueHP(self, item: str, output_path: str = "/m2m:rsp/pc/m2m:cin/con", payload=None):
        return self._requestValue(f"MNAE/{item}", output_path, payload)

    def available_services(self, unit_nr: int = 1):
        """Does a discovery of the available services on the unit

        :param unit_nr: number of the unit, normally 0..2, defaults to 1
        :type unit_nr: int, optional
        """
        d = self._requestValueHP(f"{unit_nr}/UnitProfile/la")
        if d is None:
            return None 
        return json.loads(d)

    @property
    def _unit_api(self):
        """
        .. deprecated:: Use available_services instead
        """
        return self.available_services(1)

    @property
    def adapter_model(self) -> str:
        """Returns the model of the LAN adapter.
        Ex: BRP069A61"""
        # either BRP069A61 or BRP069A62
        return self._requestValue("MNCSE-node/deviceInfo", "/m2m:rsp/pc/m2m:dvi/mod")  # "NOT /m2m:rsp/pc/m2m:cin/con"

    @property
    def unit_datetime(self) -> datetime.datetime:
        """Returns the current date of the unit. Is refreshed every minute or so"""
        d = self._requestValueHP("0/DateTime/la")
        if d is None:
            return None
        return datetime.datetime.strptime(d, self.DATETIME_FMT)

    @property
    def is_unit_datetime_adjustable(self) -> bool:
        """Returns True if the datetime of your unit is adjustable"""
        d = self._requestValueHP("0/UnitProfile/la")
        if d is None:
            return False
        j = json.loads(d)
        try:
            return j["DateTime"]["DateTimeAdjustable"]
        except KeyError:
            return None

    def set_unit_datetime(self, d: datetime.datetime) -> bool:
        """Sets the datetime of your unit. 
        Does not work on all units, see `is_unit_datetime_adjustable`

        :param d: datetime to be set
        :type d: datetime.datetime
        :return: success
        :rtype: bool
        """
        sd = datetime.datetime.strftime(d, self.DATETIME_FMT)
        payload = {
            "con": sd,
            "cnf": "text/plain:0",
        }
        return (self._requestValueHP("0/DateTime", "/", payload) is not None)

    @property
    def unit_model(self) -> str:
        """Returns the model of the heating unit.
        Ex: EAVH16S23DA6V"""
        # There should in theory also be:
        # 0/UnitInfo/ModelNumber/la, but it's not implemented (in my unit)
        # 2/UnitInfo/ModelNumber/la, but replies with the reply from 1/UnitInfo/ModelNumber/la (in my unit)
        return self._requestValueHP("1/UnitInfo/ModelNumber/la")

    @property
    def unit_type(self) -> str:
        """Returns the type of unit"""
        # same remarks as with UnitInfo/ModelNumber
        return self._requestValueHP("1/UnitInfo/UnitType/la")

    @property
    def indoor_unit_version(self) -> str:
        """Returns the unit version"""
        return self._requestValueHP("1/UnitInfo/Version/IndoorSettings/la")

    @property
    def indoor_unit_software_version(self) -> str:
        """Returns the unit software version"""
        return self._requestValueHP("1/UnitInfo/Version/IndoorSoftware/la")

    @property
    def outdoor_unit_software_version(self) -> str:
        """Returns the unit software version"""
        return self._requestValueHP("1/UnitInfo/Version/OutdoorSoftware/la")

    @property
    def remote_setting_version(self) -> str:
        """Returns the remote console setting version"""
        return self._requestValueHP("1/UnitInfo/Version/RemoconSettings/la")

    @property
    def remote_software_version(self) -> str:
        """Returns the remote console setting software version"""
        return self._requestValueHP(
            "1/UnitInfo/Version/RemoconSoftware/la")

    @property
    def pin_code(self) -> str:
        """Returns the pin code of the LAN adapter"""
        return self._requestValueHP("1/ChildLock/PinCode/la")

    @property
    def is_holiday_mode(self) -> bool:
        """ Returns if the holiday mode active or not """
        r = self._requestValueHP("1/Holiday/HolidayState/la")
        if r is None:
            return None
        return r == 1
    
    @property
    def control_mode(self) -> str:
        """ Returns the type of control used for heating. This is an installation setting."""
        # example: "ext RT control" for a contact type external room thermostat, that disables the indoor_temperature and indoor_setpoint_temperature
        return self._requestValueHP("1/UnitStatus/ControlModeState/la")

    def set_holiday_mode(self, on_holiday: bool) -> bool:
        """Whether to turn the holiday mode on(True) or off(False).
        You can confirm that it works by calling self.is_holiday_mode

        :param on_holiday: True for holiday
        :type on_holiday: bool
        :return: success
        :rtype: bool
        """
        mode_dict = {
            True: 1,
            False: 0,
        }

        payload = {
            'con': mode_dict[on_holiday],
            'cnf': 'text/plain:0',
        }

        return (self._requestValueHP("1/Holiday/HolidayState", "/", payload) is not None)

    # HOT WATER TANK STUFF
    @property
    def tank_temperature(self) -> float:
        """Returns the hot water tank temperature, in °C"""
        return self._requestValueHP("2/Sensor/TankTemperature/la")

    @property
    def tank_setpoint_temperature(self) -> float:
        """Returns the hot water tank setpoint (target) temperature, in °C"""
        return self._requestValueHP("2/Operation/TargetTemperature/la")

    @property
    def is_tank_heating_enabled(self) -> bool:
        """Returns if the tank heating is currently enabled"""
        r = self._requestValueHP("2/Operation/Power/la")
        if r is None:
            return None
        else:
            return (r == "on")

    @property
    def is_tank_powerful(self) -> bool:
        """Returns if the tank is in powerful state"""
        r = self._requestValueHP("2/Operation/Powerful/la")
        if r is None:
            return None
        else:
            return (r == 1)

    def set_tank_heating_enabled(self, powerful_active: bool) -> bool:
        """Whether to turn the water tank high/"powerful" heating on(True) or off(False).
        You can confirm that it works by calling self.is_tank_heating_enabled

        :param powerful_active: True for on
        :type powerful_active: bool
        :return: success
        :rtype: bool
        """
        mode_dict = {
            True: 1,
            False: 0,
        }
        payload = {
            "con": mode_dict[powerful_active],
            "cnf": "text/plain:0",
        }
        return (self._requestValueHP("2/Operation/Powerful", "/", payload) is not None)

    # HEATING STUFF
    @property
    def indoor_temperature(self) -> float:
        """Returns the indoor temperature, in °C"""
        return self._requestValueHP("1/Sensor/IndoorTemperature/la")

    @property
    def outdoor_temperature(self) -> float:
        """Returns the outdoor temperature, in °C"""
        return self._requestValueHP("1/Sensor/OutdoorTemperature/la")

    @property
    def indoor_setpoint_temperature(self) -> float:
        """Returns the indoor setpoint (target) temperature, in °C"""
        return self._requestValueHP("1/Operation/TargetTemperature/la")

    @property
    def leaving_water_temperature(self) -> float:
        """Returns the heating leaving water temperature, in °C"""
        return self._requestValueHP("1/Sensor/LeavingWaterTemperatureCurrent/la")

    @property
    def leaving_water_temperature_offset(self) -> float:
        """Returns the heating leaving water temperature, in °C"""
        return self._requestValueHP("1/Operation/LeavingWaterTemperatureOffsetHeating/la")
        
    def set_leaving_water_temperature_offset(self, offset_temperature_c: int) -> bool:
        """Sets the heating leaving water offset temperature, in °C

        :param offset_temperature_c: offset temperature in °C, normally in range [-10,+10]
        :type offset_temperature_c: int
        :return: success
        :rtype: bool        
        """
        payload = {
            "con": offset_temperature_c,
            "cnf": "text/plain:0",
        }
        return (self._requestValueHP("1/Operation/LeavingWaterTemperatureOffsetHeating", "/", payload) is not None)

    @property
    def is_heating_enabled(self) -> bool:
        """Returns if the unit heating is enabled"""
        r = self._requestValueHP("1/Operation/Power/la")
        if r is None:
            return None
        else:
            return (r == "on")

    @property
    def heating_mode(self) -> str:
        """Returns whether the heat pump is heating or cooling.
        """
        return self._requestValueHP("1/Operation/OperationMode/la")

    @property
    def heating_power_consumption(self) -> dict:
        """Returns the energy (electrical) consumption for heating in kWh per [D]ay, [W]eek, [M]onth"""
        return self._requestValueHP("1/Consumption/la", "m2m:rsp/pc/m2m:cin/con")

    @property
    def tank_power_consumption(self) -> dict:
        """Returns the energy (electrical) consumption for hot water in kWh per [D]ay, [W]eek, [M]onth"""
        return self._requestValueHP("2/Consumption/la", "m2m:rsp/pc/m2m:cin/con")

    def set_setpoint_temperature(self, setpoint_temperature_c: float) -> bool:
        """Sets the heating setpoint (target) temperature, in °C

        :param setpoint_temperature_c: target temperature, in °C
        :type setpoint_temperature_c: float
        :return: success
        :rtype: bool
        """
        payload = {
            "con": setpoint_temperature_c,
            "cnf": "text/plain:0",
        }
        return (self._requestValueHP("1/Operation/TargetTemperature", "/", payload) is not None)

    def set_heating_enabled(self, heating_active: bool) -> bool:
        """Whether to turn the heating on(True) or off(False).
        You can confirm that it works by calling self.is_heating_enabled

        :param heating_active: True: turn the heating on
        :type heating_active: bool
        :return: success
        :rtype: bool
        """
        mode_dict = {
            True: "on",
            False: "standby",
        }
        payload = {
            "con": mode_dict[heating_active],
            "cnf": "text/plain:0",
        }
        return (self._requestValueHP("1/Operation/Power", "/", payload) is not None)

    @property
    def heating_schedule(self) -> list[HeatingSchedule]:
        """Returns the HeatingSchedule list heating"""
        d = self._requestValueHP(
            "1/Schedule/List/Heating/la")
        if d is None:
            return []
        j = json.loads(d)

        out_schedules = []
        for schedule in j["data"]:
            out_schedules.append(self._unmarshall_schedule(schedule, DaikinAltherma._heating_value_parser))
        return out_schedules

    @property
    def is_heating_error(self) -> bool:
        """Returns if the heating has an error"""
        r = self._requestValueHP("1/UnitStatus/ErrorState/la")
        if r is None:
            return None
        else:
            return (r == 1)
        
    @property
    def is_heating_warning(self) -> bool:
        """Returns if the heating has a warning"""
        r = self._requestValueHP("1/UnitStatus/WarningState/la")
        if r is None:
            return None
        else:
            return (r == 1)        

    @property
    def is_heating_active(self) -> bool:
        """Returns if the heating is currently active"""
        r = self._requestValueHP("1/UnitStatus/ActiveState/la")
        if r is None:
            return None
        else:
            return (r == 1)

    @property
    def is_heating_emergency(self) -> bool:
        """Returns if the heating is in emergency state"""
        r = self._requestValueHP("1/UnitStatus/EmergencyState/la")
        if r is None:
            return None
        else:
            return (r == 1)
        
    @property
    def in_installerstate(self) -> bool:
        """Returns if the heating is in the installer mode, will have limited functionality in that case"""
        r = self._requestValueHP("1/UnitStatus/InstallerState/la")
        if r is None:
            return None
        else:
            return (r == 1)

    @property
    def tank_schedule(self) -> list[TankSchedule]:
        """Returns the TankSchedule list heating"""
        d = self._requestValueHP("2/Schedule/List/Heating/la")
        j = json.loads(d)
        if j is None:
            return []

        def value_parser(x):
            return TankStateEnum.int_to_state(x)

        out_schedules = []
        for schedule in j["data"]:
            out_schedules.append(self._unmarshall_schedule(schedule, value_parser))
        return out_schedules

    def set_heating_schedule(self, schedule: HeatingSchedule) -> bool:
        """Sets the heating schedule for the heating.

        :param schedule: the schedule to set
        :type schedule: HeatingSchedule
        :return: success
        :rtype: bool
        """
        schedule_str = self._marshall_schedule(schedule)
        dq = {"data": [schedule_str]}

        payload = {
            "con": json.dumps(dq),
            "cnf": "text/plain:0",
        }
        self._requestValueHP("1/Schedule/List/Heating", "/", payload)

    @property
    def heating_schedule_state(self) -> HeatingScheduleState:
        """Returns the actual heating schedule state"""
        d = self._requestValueHP("1/Schedule/Next/la")
        if d is None:
            return None
        j = json.loads(d)
        dq = j['data']

        return HeatingScheduleState(
            OperationMode=dq['OperationMode'],
            StartTime=dq['StartTime'],
            TargetTemperature=DaikinAltherma._heating_value_parser(dq['TargetTemperature']),
            Day=dq['Day'],
        )

    @property
    def tank_schedule_state(self) -> TankScheduleState:
        """Returns the actual tank schedule state"""
        d = self._requestValueHP("2/Schedule/Next/la")
        if d is None:
            return None
        j = json.loads(d)
        dq = j['data']

        return TankScheduleState(
            OperationMode=dq['OperationMode'],
            StartTime=dq['StartTime'],
            TankState=TankStateEnum.int_to_state(dq['TargetTemperature']),  # Copy paste powa
            Day=dq['Day'],
        )

    @property
    def is_tank_error(self) -> bool:
        """Returns if the tank has an error"""
        r = self._requestValueHP("2/UnitStatus/ErrorState/la")
        if r is None:
            return None
        else:
            return (r == 1)
        
    @property
    def is_tank_warning(self) -> bool:
        """Returns if the tank has a warning"""
        r = self._requestValueHP("2/UnitStatus/WarningState/la")
        if r is None:
            return None
        else:
            return (r == 1)        

    @property
    def is_tank_active(self) -> bool:
        """Returns if the tank is currently active"""
        r = self._requestValueHP("2/UnitStatus/ActiveState/la")
        if r is None:
            return None
        else:
            return (r == 1)
        
    @property
    def is_tank_emergency(self) -> bool:
        """Returns if the tank is in emergency state"""
        r = self._requestValueHP("2/UnitStatus/EmergencyState/la")
        if r is None:
            return None
        else:
            return (r == 1)
        
    @property
    def tank_in_installerstate(self) -> bool:
        """Returns if the tank heating is in the installer mode, will have limited functionality in that case"""
        r = self._requestValueHP("2/UnitStatus/InstallerState/la")
        if r is None:
            return None
        else:
            return (r == 1)
    
    @property
    def heating_error_status(self) -> str:
        """Returns the heating status: OK or Warning or Error or Emergency"""
        e = self.is_heating_emergency
        if e is None: 
            return None
        if e:
            return "Emergency"
        e = self.is_heating_error
        if e is None: 
            return None
        if e:
            return "Error"
        e = self.is_heating_warning
        if e is None: 
            return None
        if e:
            return "Warning"
        return "OK"
    
    @property
    def tank_error_status(self) -> str:
        """Returns the tank status: OK or Warning or Error or Emergency"""
        e = self.is_tank_emergency
        if e is None: 
            return None
        if e:
            return "Emergency"
        e = self.is_tank_error
        if e is None: 
            return None
        if e:
            return "Error"
        e = self.is_tank_warning
        if e is None: 
            return None
        if e:
            return "Warning"
        return "OK"    
        
    def print_all_status(self, without_schedule: bool = False):
        def ns(x):
            return x if x is not None else "--not supported--"
        
        print(
            f"""
Daikin adapter: {ns(self.adapter_ip)} {ns(self.adapter_model)}
Daikin unit: {ns(self.unit_model)} {ns(self.unit_type)}
Daikin time: {ns(self.unit_datetime)} (adjustable: {ns(self.is_unit_datetime_adjustable)})
Software versions:
    Indoor: {ns(self.indoor_unit_software_version)}
    Outdoor: {ns(self.outdoor_unit_software_version)}
    Remote settings: {ns(self.remote_setting_version)}
    Remote software: {ns(self.remote_software_version)}
    Pin code: {ns(self.pin_code)}
Hot water tank:
    Current: {ns(self.tank_temperature)}°C (target {ns(self.tank_setpoint_temperature)}°C)
    Heating enabled: {ns(self.is_tank_heating_enabled)} (Powerful: {ns(self.is_tank_powerful)}) (Active: {ns(self.is_tank_active)})
    Status: {ns(self.heating_error_status)}
    Schedules: {"(excluded from print)" if without_schedule else ns(self.tank_schedule)}
    Schedule state: {ns(self.tank_schedule_state)}
    Consumption: {ns(self.tank_power_consumption)}
    Installer state: {ns(self.tank_in_installerstate)}
Heating:
    Control mode: {ns(self.control_mode)}
    Outdoor temp: {ns(self.outdoor_temperature)}°C
    Indoor temp: {ns(self.indoor_temperature)}°C (target {ns(self.indoor_setpoint_temperature)}°C)
    Heating enabled: {ns(self.is_heating_enabled)} (Active: {ns(self.is_heating_active)})
    Status: {ns(self.tank_error_status)}
    Leaving water: {ns(self.leaving_water_temperature)}°C
    Leaving water offset: {ns(self.leaving_water_temperature_offset)}°C
    Heating mode: {ns(self.heating_mode)}
    Schedules: {"(excluded from print)" if without_schedule else ns(self.heating_schedule)}
    Schedule state: {ns(self.heating_schedule_state)}
    Consumption: {ns(self.heating_power_consumption)}
    Installer state: {ns(self.in_installerstate)}
Holiday mode: {ns(self.is_holiday_mode)}
    """
        )

    @staticmethod
    def _unmarshall_schedule(schedule_str: str, value_parser: Callable):
        """Converts a schedule string to a schedule dict.
        The dict keys are the days (DaikinAltherma.DAYS), and the
        values are a dict of hour (HHMM) -> Setpoint T°
        Ex: {'Mo': {'0000': 23.4}}"""

        hrs = schedule_str.split("|")[2].split(";")
        i = 0
        schedule = {}

        for day in DaikinAltherma.DAYS:
            schedule_wk = {}
            temps = hrs[i: i + 6]
            for c in temps:
                ctime, cval = c.split(",")
                if ctime == "":
                    continue
                if cval == "":
                    # For some reason, the time is declared but not the value.. ?
                    continue
                val = value_parser(cval)
                schedule_wk[ctime] = val

            i += 6
            schedule[day] = schedule_wk
        return schedule

    @staticmethod
    def _marshall_schedule(schedule) -> str:
        """' Converts a schedule dict to a Daikin schedule string"""
        week_schedule = []
        for day in DaikinAltherma.DAYS:
            sday = schedule.get(day, {})
            schedule_day = []

            assert len(sday) <= 6
            for hour in sorted(sday.keys()):
                schedule_day.append(f"{hour},{int(sday[hour] * 10)}")
            padding_schedule = 6 - len(schedule_day)
            schedule_day += [","] * padding_schedule
            week_schedule += schedule_day
        schedule_str = "$NULL|1|" + ";".join(week_schedule)
        return schedule_str


if __name__ == "__main__":
    ad = DaikinAltherma("192.168.11.100")
    ad.print_all_status()
    import pprint

    pprint.pprint(ad._unit_api)
