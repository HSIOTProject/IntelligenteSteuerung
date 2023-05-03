from typing import *
from enum import Enum
import datetime
from abc import ABC, abstractmethod


class SteuerStatus(Enum):
    EIN = "ein" # Soll ein bleiben oder eingeschaltet werden
    AUS = "aus" # Soll aus bleiben oder ausgeschaltet werden
    KEEP_STATE = "keep_state" # Soll in aktuellem Zustand bleiben


class SteurElement(ABC):
    @abstractmethod
    def getConsumptionWatt(self) -> float:
        pass
    
    @abstractmethod
    def getMinActiveTimeSeconds(self):
        pass

    @abstractmethod
    def steuerung(self, data, überschuss) -> SteuerStatus:
        pass

    

class Wärmepumpe(SteurElement):
    def __init__(self):
        self.consumption = 3000
        

    def getConsumptionWatt(self) -> float:
        return self.consumption
        
    def getMinActiveTimeSeconds(self):
        return 60 * 15
    
    def steuerung(self, data, überschuss) -> SteuerStatus:
        socHouseBattery = data["e3dc"]["stateOfCharge"]
        productionGrid = data["e3dc"]["production"]["grid"]
        überschuss = (productionGrid * -1) if productionGrid < 0 else 0
        
        if (socHouseBattery > 70) or (überschuss > self.consumption):
            return SteuerStatus.EIN
        elif (socHouseBattery < 35) or (überschuss < self.consumption):
            return SteuerStatus.AUS
        return SteuerStatus.KEEP_STATE


class Wallbox(SteurElement):
    def __init__(self, wallboxId: str):
        self.wallboxId = wallboxId
        self.consumption = 3680 # Watt (16A * 230V)
    
    def getConsumptionWatt(self) -> float:
        return self.consumption
        
    def getMinActiveTimeSeconds(self):
        return 60 * 5

    def wallboxStatus(self, wbPlugged, überschuss):
        if wbPlugged:
            if (überschuss > self.maxLeistungWallbox):
                return SteuerStatus.EIN
            else:
                return SteuerStatus.AUS
    
    def steuerung(self, data, überschuss) -> SteuerStatus:
        wallboxDataKey = "wallbox"+self.wallboxId.capitalize()
        socHouseBattery = data["e3dc"]["stateOfCharge"]
        plugged = data[wallboxDataKey]["plugged"]

        if plugged:
            if (überschuss > self.consumption) and (socHouseBattery > 30):
                return SteuerStatus.EIN
            else:
                return SteuerStatus.AUS
        
        return SteuerStatus.KEEP_STATE


STATE = {
    "wallboxLinks": {
        "timestampActivated": None,
    },
    "wallboxRechts": {
        "timestampActivated": None,
    },
    "wärmepumpe": {
        "timestampActivated": None,
    }
}


def sterung(data, now: datetime.datetime=None):
    if not now:
        now = datetime.datetime.now()
    productionGrid = data["e3dc"]["production"]["grid"]
    überschuss = (productionGrid * -1) if productionGrid < 0 else 0
    komponenten = {
        "wallboxLinks": Wallbox("links"),
        "wallboxRechts": Wallbox("rechts"),
        "wärmepumpe": Wärmepumpe(),
    }
    
    steuerStatus = {}

    for key, value in komponenten.items():
        timestampActivate = STATE[key]["timestampActivated"] 
        timestampNextAllowedAction = timestampActivate + datetime.timedelta(seconds=value.getMinActiveTimeSeconds()) if timestampActivate else None
        if timestampActivate and now < timestampNextAllowedAction:
            steuerStatus[key] = SteuerStatus.KEEP_STATE
            continue
        status = value.steuerung(data, überschuss)
        if status == SteuerStatus.EIN:
            STATE[key]["timestampActivated"] = now
            überschuss = überschuss - value.getConsumptionWatt()
        elif status == SteuerStatus.AUS:
            pass
        elif status == SteuerStatus.KEEP_STATE:
            pass
        else:
            # Worst case szenario is that the program turns on too many devices consuming too much power costing money for the energy from the grid better to just trow an error and make clear something went wrong
            raise Exception("Unknown SteuerStatus")
        steuerStatus[key] = status.value
        
    return steuerStatus
