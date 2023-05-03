from typing import *
from enum import Enum


class SteuerStatus(Enum):
    EIN = "ein" # Soll ein bleiben oder eingeschaltet werden
    AUS = "aus" # Soll aus bleiben oder ausgeschaltet werden
    KEEP_STATE = "keep_state" # Soll in aktuellem Zustand bleiben


def sterung(data):
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
    
    statusWärmepumpe = SteuerStatus.KEEP_STATE
    
    if (socHouseBattery > 70) or (überschuss > consumptionWärmepumpe):
        statusWärmepumpe = SteuerStatus.EIN
    elif (socHouseBattery < 35) or (überschuss < consumptionWärmepumpe):
        statusWärmepumpe = SteuerStatus.AUS
    
    
    return {
        "wärmepumpe": statusWärmepumpe.value,
        "wallboxLinks": SteuerStatus.KEEP_STATE.value,
        "wallboxRechts": SteuerStatus.KEEP_STATE.value,
    }
