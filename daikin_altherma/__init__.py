import json
from typing import Callable
from dataclasses import dataclass
import enum
import logging
import time
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
    Day: str ## XXX enum

@dataclass
class HeatingScheduleState(_ScheduleState):
    TargetTemperature: float

@dataclass
class TankScheduleState(_ScheduleState):
    TankState: TankStateEnum


class DaikinAltherma:
    UserAgent = "python-daikin-altherma"
    DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    _heating_value_parser = lambda x: float(x)/10
    DATETIME_FMT = "%Y%m%dT%H%M%SZ"

    def __init__(self, adapter_ip: str):
        self.adapter_ip = adapter_ip
        self.ws = create_connection(f"ws://{self.adapter_ip}/mca")

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
        except:
            logging.error("Could not get data. Maybe the unit is starting up?")
            raise

    def _requestValueHP(self, item: str, output_path: str, payload=None):
        return self._requestValue(f"MNAE/{item}", output_path, payload)

    @property
    def _unit_api(self):
        return json.loads(
            self._requestValueHP("1/UnitProfile/la", "/m2m:rsp/pc/m2m:cin/con")
        )

    @property
    def adapter_model(self) -> str:
        """Returns the model of the LAN adapter.
        Ex: BRP069A61"""
        # either BRP069A61 or BRP069A62
        return self._requestValue("MNCSE-node/deviceInfo", "/m2m:rsp/pc/m2m:dvi/mod")

    @property
    def unit_datetime(self) -> datetime.datetime:
        """Returns the current date of the unit. Takes time to refresh"""
        d = self._requestValueHP("0/DateTime/la", "/m2m:rsp/pc/m2m:cin/con")
        return datetime.datetime.strptime(d, self.DATETIME_FMT)

    @property
    def unit_model(self) -> str:
        """Returns the model of the heating unit.
        Ex: EAVH16S23DA6V"""
        return self._requestValueHP(
            "1/UnitInfo/ModelNumber/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def unit_type(self) -> str:
        """Returns the type of unit"""
        return self._requestValueHP("1/UnitInfo/UnitType/la", "/m2m:rsp/pc/m2m:cin/con")

    @property
    def indoor_unit_version(self) -> str:
        """Returns the unit version"""
        return self._requestValueHP(
            "1/UnitInfo/Version/IndoorSettings/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def indoor_unit_software_version(self) -> str:
        """Returns the unit software version"""
        return self._requestValueHP(
            "1/UnitInfo/Version/IndoorSoftware/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def outdoor_unit_software_version(self) -> str:
        """Returns the unit software version"""
        return self._requestValueHP(
            "1/UnitInfo/Version/OutdoorSoftware/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def remote_setting_version(self) -> str:
        """Returns the remote console setting version"""
        return self._requestValueHP(
            "1/UnitInfo/Version/RemoconSettings/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def remote_software_version(self) -> str:
        """Returns the remote console setting software version"""
        return self._requestValueHP(
            "1/UnitInfo/Version/RemoconSoftware/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def pin_code(self) -> str:
        """Returns the pin code of the LAN adapter"""
        return self._requestValueHP("1/ChildLock/PinCode/la", "/m2m:rsp/pc/m2m:cin/con")

    # HOT WATER TANK STUFF
    @property
    def tank_temperature(self) -> float:
        """Returns the hot water tank temperature, in °C"""
        return self._requestValueHP(
            "2/Sensor/TankTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def tank_setpoint_temperature(self) -> float:
        """Returns the hot water tank setpoint (target) temperature, in °C"""
        return self._requestValueHP(
            "2/Operation/TargetTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def is_tank_heating_enabled(self) -> bool:
        """Returns if the tank heating is currently enabled"""
        return (
            self._requestValueHP("2/Operation/Power/la", "m2m:rsp/pc/m2m:cin/con")
            == "on"
        )

    @property
    def is_tank_powerful(self) -> bool:
        """Returns if the tank is in powerful state"""
        return (
            self._requestValueHP("2/Operation/Powerful/la", "m2m:rsp/pc/m2m:cin/con")
            == 1
        )

    def set_tank_heating_enabled(self, powerful_active: bool):
        """Whether to turn the water tank heating on(True) or off(False).
        You can confirm that it works by calling self.is_tank_heating_enabled
        """
        mode_dict = {
            True: 1,
            False: 0,
        }

        payload = {
            "con": mode_dict[powerful_active],
            "cnf": "text/plain:0",
        }

        self._requestValueHP("2/Operation/Powerful", "/", payload)

    # HEATING STUFF
    @property
    def indoor_temperature(self) -> float:
        """Returns the indoor temperature, in °C"""
        return self._requestValueHP(
            "1/Sensor/IndoorTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def outdoor_temperature(self) -> float:
        """Returns the outdoor temperature, in °C"""
        return self._requestValueHP(
            "1/Sensor/OutdoorTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def indoor_setpoint_temperature(self) -> float:
        """Returns the indoor setpoint (target) temperature, in °C"""
        return self._requestValueHP(
            "1/Operation/TargetTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def leaving_water_temperature(self) -> float:
        """Returns the heating leaving water temperature, in °C"""
        return self._requestValueHP(
            "1/Sensor/LeavingWaterTemperatureCurrent/la", "m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def is_heating_enabled(self) -> bool:
        """Returns if the unit heating is enabled"""
        return (
            self._requestValueHP("1/Operation/Power/la", "m2m:rsp/pc/m2m:cin/con")
            == "on"
        )

    @property
    def heating_mode(self) -> str:
        """This function name makes no sense, because it
        returns whether the heat pump is heating or cooling.
        """
        return self._requestValueHP(
            "1/Operation/OperationMode/la", "m2m:rsp/pc/m2m:cin/con"
        )

    @property
    def power_consumption(self) -> dict:
        """Returns the energy consumption in kWh per [D]ay, [W]eek, [M]onth"""
        return self._requestValueHP("1/Consumption/la", "m2m:rsp/pc/m2m:cin/con")

    def set_setpoint_temperature(self, setpoint_temperature_c: float):
        """Sets the heating setpoint (target) temperature, in °C"""
        payload = {
            "con": setpoint_temperature_c,
            "cnf": "text/plain:0",
        }

        self._requestValueHP("1/Operation/TargetTemperature", "/", payload)

    def set_heating_enabled(self, heating_active: bool):
        """Whether to turn the heating on(True) or off(False).
        You can confirm that it works by calling self.is_heating_enabled
        """
        mode_dict = {
            True: "on",
            False: "standby",
        }

        payload = {
            "con": mode_dict[heating_active],
            "cnf": "text/plain:0",
        }

        self._requestValueHP("1/Operation/Power", "/", payload)

    @property
    def heating_schedule(self) -> list[HeatingSchedule]:
        """Returns the HeatingSchedule list heating"""
        d = self._requestValueHP(
            "1/Schedule/List/Heating/la", "/m2m:rsp/pc/m2m:cin/con"
        )
        j = json.loads(d)

        out_schedules = []
        for schedule in j["data"]:
            out_schedules.append(self._unmarshall_schedule(schedule, DaikinAltherma._heating_value_parser))
        return out_schedules

    @property
    def tank_schedule(self) -> list[TankSchedule]:
        """Returns the TankSchedule list heating"""
        d = self._requestValueHP(
            "2/Schedule/List/Heating/la", "/m2m:rsp/pc/m2m:cin/con"
        )
        j = json.loads(d)

        def value_parser(x):
            return TankStateEnum.int_to_state(x)

        out_schedules = []
        for schedule in j["data"]:
            out_schedules.append(self._unmarshall_schedule(schedule, value_parser))
        return out_schedules

    def set_heating_schedule(self, schedule: HeatingSchedule):
        """Sets the heating schedule for the heating."""
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
        d = self._requestValueHP("1/Schedule/Next/la", "/m2m:rsp/pc/m2m:cin/con")
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
        d = self._requestValueHP("2/Schedule/Next/la", "/m2m:rsp/pc/m2m:cin/con")
        j = json.loads(d)
        dq = j['data']

        return TankScheduleState(
            OperationMode=dq['OperationMode'],
            StartTime=dq['StartTime'],
            TankState=TankStateEnum.int_to_state(dq['TargetTemperature']),  #Copy paste powa
            Day=dq['Day'],
        )


    def print_all_status(self):
        print(
            f"""
Daikin adapter: {self.adapter_ip} {self.adapter_model}
Daikin unit: {self.unit_model} {self.unit_type}
Daikin time: {self.unit_datetime}
Hot water tank:
    Current: {self.tank_temperature}°C (target {self.tank_setpoint_temperature}°C)
    Heating enabled: {self.is_tank_heating_enabled} (Powerful: {self.is_tank_powerful})
    Schedule: {self.tank_schedule[0]}
    Schedule state: {self.tank_schedule_state}
Heating:
    Outdoor temp:{self.outdoor_temperature}°C
    Indoor temp: {self.indoor_temperature}°C
    Heating target: {self.indoor_setpoint_temperature}°C (is heating enabled: {self.is_heating_enabled})
    Leaving water: {self.leaving_water_temperature}°C
    Heating mode: {self.heating_mode}
    Schedule: {self.heating_schedule[0]}
    Schedule state: {self.heating_schedule_state}
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
            temps = hrs[i : i + 6]
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
                schedule_day.append(f"{hour},{int(sday[hour]*10)}")
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
