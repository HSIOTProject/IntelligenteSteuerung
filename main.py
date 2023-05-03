import logging
import os
from typing import *
from jsonrpcx import *
import datetime
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
        return steuerung.sterung(data, datetime.datetime.now())

   

class Delegate(ASGIServerDelegate):
    def HTMLHeaders(self) -> List[str]:
        return [("Content-Type", "application/json")]


async def app(scope, receive, send):
    rpcServer = Service(delegate=Delegate())
    return await rpcServer.parseRequest(scope, receive, send)
