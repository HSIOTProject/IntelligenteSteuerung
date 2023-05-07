import logging
import os
from typing import *
from jsonrpcx import *
import steuerung

logging.basicConfig(level=logging.DEBUG)


class Service(ASGIServer):
    async def ping(self) -> str:
        return "pong"

    async def update(self):
        code = os.system("git pull")
        return {
            "reutn_code": code
        }
        
    async def steuerung(self, data):
        return steuerung.sterung(data)

    async def _rcCall(self, auth, method, params=[]):
        with open("config.json") as f:
            config = json.load(f)
            mqttConfig = config["mqtt"]
        if auth == config["auth"]:
            return await mqttRPCCall(method, params,
                                mqttHost=mqttConfig["host"],
                                mqttUser=mqttConfig["user"],
                                mqttPassword=mqttConfig["password"],
                                mqttPort=mqttConfig["port"],
                                mqttTopic=mqttConfig["topic"])
        raise Exception("Auth failed")
    
    async def rcPing(self, auth) -> str:
        return await self._rcCall(auth, "ping")
    
    async def rcMethodCall(self, auth: str, method: str, params=[]):
        return await self._rcCall(auth, method, params)



class Delegate(ASGIServerDelegate):
    def HTMLHeaders(self) -> List[str]:
        return [("Content-Type", "application/json")]


async def app(scope, receive, send):
    rpcServer = Service(delegate=Delegate())
    return await rpcServer.parseRequest(scope, receive, send)
