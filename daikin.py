import json
import uuid

from websocket import create_connection
import dpath.util


class DaikinAltherma:
    UserAgent = "python-daikin-altherma"

    def __init__(self, adapter_ip: str):
        self.adapter_ip = adapter_ip
        self.ws = create_connection(f"ws://{self.adapter_ip}/mca")

    def _requestValue(self, item: str, output_path: str):
        reqid = uuid.uuid4().hex[0:5]
        js_request = {
            "m2m:rqp": {
                "fr": DaikinAltherma.UserAgent,
                "rqi": reqid,
                "op": 2,
                "to": f"/[0]/{item}",
            }
        }
        self.ws.send(json.dumps(js_request))
        result = json.loads(self.ws.recv())

        assert result["m2m:rsp"]["rqi"] == reqid
        assert result["m2m:rsp"]["to"] == DaikinAltherma.UserAgent

        return dpath.util.get(result, output_path)

    def _requestValueHP(self, item: str, output_path: str):
        return self._requestValue(f"MNAE/{item}", output_path)

    def function(self):
        return self._requestValue("MNAE/", "/m2m:rsp/pc/m2m:cnt/lbl")

    def adapter_model(self) -> str:
        return self._requestValue("MNCSE-node/deviceInfo", "/m2m:rsp/pc/m2m:dvi/mod")

    def tank_temperature(self) -> float:
        return self._requestValueHP(
            "2/Sensor/TankTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    def indoor_temperature(self) -> float:
        return self._requestValueHP(
            "1/Sensor/IndoorTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    def outdoor_temperature(self) -> float:
        return self._requestValueHP(
            "1/Sensor/OutdoorTemperature/la", "/m2m:rsp/pc/m2m:cin/con"
        )

    def leaving_water_temperature(self) -> float:
        return self._requestValueHP(
            "1/Sensor/LeavingWaterTemperatureCurrent/la", "m2m:rsp/pc/m2m:cin/con"
        )

    def power_state(self) -> str:
        return self._requestValueHP("1/Operation/Power/la", "m2m:rsp/pc/m2m:cin/con")

    def power_consumption(self) -> dict:
        return self._requestValueHP("1/Consumption/la", "m2m:rsp/pc/m2m:cin/con")


if __name__ == "__main__":
    ad = DaikinAltherma("192.168.10.126")
    print(ad.adapter_model())
    print(ad.function())
    print(ad.tank_temperature())
    print(ad.outdoor_temperature())
    print(ad.indoor_temperature())
    print(ad.leaving_water_temperature())
    print(ad.power_state())
    print(ad.power_consumption())
