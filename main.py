import logging
import os
from typing import *
from jsonrpcx import *
from enum import Enum

logging.basicConfig(level=logging.DEBUG)

class SteuerStatus(Enum):
    EIN = "ein" # Soll ein bleiben oder eingeschaltet werden
    AUS = "aus" # Soll aus bleiben oder ausgeschaltet werden
    KEEP_STATE = "keep_state" # Soll in aktuellem Zustand bleiben


class Service(ASGIServer):
    async def ping(self) -> str:
        return "pong"
    
    async def update(self):
        code = os.system("git pull")
        return {
            "reutn_code": code
        }
    
    async def sterung(self, data):
        # TODO: Get data from InfluxDB
        socHouseBattery = data["e3dc"]["stateOfCharge"]
        wbLinksPlugged = data["wallboxLinks"]["plugged"]
        wbLinksChargingActive = data["wallboxLinks"]["chargingActive"]
        wbRechtsPlugged = data["wallboxRechts"]["plugged"]
        wbRechtsChargingActive = data["wallboxRechts"]["chargingActive"]
        wpStatus = data["wärmepumpe"]["status"]
        productionSolarTotal = data["e3dc"]["production"]["solar"] + data["e3dc"]["production"]["add"]
        productionGrid = data["e3dc"]["production"]["grid"]
        überschuss = (productionGrid * -1) if productionGrid < 0 else 0
        consumptionWärmepumpe = 3000
        
        statusWärmepumpe = None
        
        if (socHouseBattery > 70) and (überschuss > consumptionWärmepumpe):
            statusWärmepumpe = SteuerStatus.EIN.value
        elif (socHouseBattery < 35) or (überschuss < consumptionWärmepumpe):
            statusWärmepumpe = SteuerStatus.AUS.value
        
        return {
            "wärmepumpe": statusWärmepumpe,
            "wallboxLinks": SteuerStatus.KEEP_STATE.value,
            "wallboxRechts": SteuerStatus.KEEP_STATE.value,
        }

class Delegate(ASGIServerDelegate):
    def HTMLHeaders(self) -> List[str]:
        return [("Content-Type", "application/json")]


async def app(scope, receive, send):
    rpcServer = Service(delegate=Delegate())
    return await rpcServer.parseRequest(scope, receive, send)
