"""Exalus API"""

from typing import Any
from enum import Enum
import asyncio
import logging
import uuid
import requests
import events

from json import dumps, loads
from dataclasses import dataclass, asdict

from signalrcore.hub_connection_builder import HubConnectionBuilder

SERVER_BROKER_URL: str = "http://broker.tr7.pl"

_LOGGER = logging.getLogger(__name__)

@dataclass
class DataFrame: #DataFrame class to communicate with the controller
    Resource: str
    Status: Enum
    Method: Enum
    TransactionId: uuid
    Data: Any


class Method(Enum): #Method class created to be injected in dataframes
    Get = 0
    Post = 1
    Delete = 2
    Put = 3
    Options = 4
    Head = 5


class Status(Enum): #Status class created to be injected in dataframes
    OK = 0
    UnknownError = 1
    FatalError = 2
    WrongData = 3
    ResourceDoesNotExist = 4
    NoPermissionToPerformThisOperation = 5
    SessionHasAlreadyLoggedOnUser = 6
    OperationNotPermitted = 7
    NoPersmissionsToCallGiverResource = 8
    ResourceIsNotAvailable = 9
    Error = 10
    NoData = 11
    NotSupportedMethod = 12
    UserNotLoggedIn = 13


class ExalusAPIClient:
    
    """
    Main API class
    _summary_
    """
    def __init__(self, controller_serial, controller_pin, login, password):
        self.controller_serial: str = controller_serial
        self.controller_pin: str = controller_pin
        self.server_uri: str = ""
        self.hub_connection: None or HubConnectionBuilder = None
        self.login: str = login
        self.password: str = password
        self.is_authorized = False
        self.last_response = None
        self.devices_list = None

    def data_parser(self, resp):
        """_summary_

        Args:
            resp (_type_): _description_
            event (_type_): _description_

        Returns:
            _type_: _description_
        """
        obj = loads(resp[1])
        return obj

    async def process_data(self, event):
        """_summary_

        Args:
            event (_type_): _description_
        """
        try:
            async with asyncio.wait(10):
                await event.wait()
        except asyncio.TimeoutError():
            print("Timeout!")
            return
        event.clear()

    async def authorize_async(self, auth_result):
        """_summary_

        Args:
            auth_result (_type_): _description_
        """
        if auth_result:
            login_frame = DataFrame(
                "/users/user/login",
                Status.WrongData.value,
                Method.Put.value,
                str(uuid.uuid1()),
                {"Email": self.login, "Password": self.password},
            )
            await self.send_and_wait(login_frame)
        else:
            print("Authorization falied!")

    def authorize(self, auth_result):
        """_summary_

        Args:
            auth_result (_type_): _description_
        """
        asyncio.run(self.authorize_async(auth_result))
                
    def establish_connection(self) -> None:
        """Main function used for connecting with controller and handle callbacks"""

        result = requests.get(
            f"{SERVER_BROKER_URL}/api/connections/broker/whichserver/{self.controller_serial}",
            timeout=5000,
        )
        print(result)
        if result.status_code != 200:
            raise requests.exceptions.ConnectionError

        else:
            print("Broker address has been acquired!")

            self.server_uri = f"https://{result.text}/broker"

            print(self.server_uri)

            self.hub_connection = (
                HubConnectionBuilder()
                .with_url(self.server_uri)
                .configure_logging(logging.INFO)
                .with_automatic_reconnect(
                    {
                        "type": "raw",
                        "keep_alive_interval": 10,
                        "reconnect_interval": 5,
                        "max_attempts": 5,
                    }
                )
                .build()
            )

            self.hub_connection.on("SendError", print)
            self.hub_connection.on("Authorization", self.authorize)
            self.hub_connection.on("Registration", print)
            self.hub_connection.on("Data", lambda data: self.data_parser(data))
            self.hub_connection.on_open(self.start)
            self.hub_connection.start()

    async def send_and_wait(self, sent_frame: DataFrame, ms_timeout=5000):
        """_summary_

        Args:
            sent_frame (DataFrame): _description_
            ms_timeout (int, optional): _description_. Defaults to 5000.
        """
        ack_event = asyncio.Event()

        print("Sent frame", sent_frame)

        def ack_received(response):
            recieved_frame = self.data_parser(response)
            print(recieved_frame["TransactionId"], sent_frame.TransactionId)
            if recieved_frame["TransactionId"] == sent_frame.TransactionId:
                ack_event.set()

        self.hub_connection.on("Data", ack_received)
        self.hub_connection.send(
            "SendTo", [self.controller_serial, asdict(sent_frame)]
        )

        try:
            await asyncio.wait_for(ack_event.wait(), timeout=ms_timeout / 1000)

        except asyncio.TimeoutError:
            print("Timeout error!")

    def start(self):
        """_summary_
        """
        self.hub_connection.send(
            "AuthorizeTo", [self.controller_serial, self.controller_pin]
        )

    def send_frame(self, data_frame: DataFrame) -> None:
        """Send frame to controller"""

        self.hub_connection.send("SendTo", [self.controller_serial, data_frame])