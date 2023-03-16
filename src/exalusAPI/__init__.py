import asyncio, logging, uuid, requests

from json import dumps, loads
from dataclasses import dataclass, asdict
from typing import Any
from events import Events
from enum import Enum
from signalrcore.hub_connection_builder import HubConnectionBuilder

SERVER_BROKER_URL: str = "http://broker.tr7.pl"

_LOGGER = logging.getLogger(__name__)


# Frame declaration
@dataclass
class DataFrame:
    Resource: str
    Status: Enum
    Method: Enum
    TransactionId: uuid
    Data: Any


class Method(Enum):
    Get = 0
    Post = 1
    Delete = 2
    Put = 3
    Options = 4
    Head = 5


class Status(Enum):
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


class ConnectionError(Exception):
    """Raised when connection error."""

    def __init__(self, message: str = "Connection error!") -> None:
        """Init"""
        super().__init__(message)
        self.message = message


class Controller:
    def __init__(self, controller_serial, controller_pin, login, password):
        self.controller_serial: str = controller_serial

        self.controller_pin: int = controller_pin

        self.server_uri: str = ""

        self.hub_connection: None or HubConnectionBuilder = None

        self._on_receive: Events = Events

        self.login: str = login

        self.password: str = password

    def start(self) -> None:
        """Authorize user"""

        self.hub_connection.send(
            "AuthorizeTo", [self.controller_serial, self.controller_pin]
        )

    def auth_result(self, auth_result) -> None:
        """Check if user has been authorized"""

        if auth_result:
            _LOGGER.info("User has been authorized")

            frame = dumps(
                asdict(
                    DataFrame(
                        "/users/user/login",
                        Status.WrongData.value,
                        Method.Put.value,
                        str(uuid.uuid1()),
                        {"Email": self.login, "Password": self.password},
                    )
                )
            )

            _LOGGER.info("Sent frame: %s", frame)

            self.send_frame(frame)

        else:
            _LOGGER.info("Authorization failed!")

    async def send_and_wait_for_response(
        self, dataframe: DataFrame, ms_timeout: int = 5000
    ) -> DataFrame:
        """Send frames and wait for response"""

        result = asyncio.Future()

        def on_response_received(frame: DataFrame):
            if frame.TransactionId == dataframe.TransactionId:
                self._on_receive.on_change -= on_response_received

                result.set_result(frame)

        self.send_frame()

        self._on_receive.on_change += on_response_received

        await asyncio.wait_for(result, timeout=ms_timeout)

        return result.result

    def data_handler(self, data: list) -> None:
        """Handle incoming data"""

        frame = loads(data[1])

        if frame["Resource"] != "/homemessaging/notify/message/new":
            _LOGGER.info("Sent by: %s data:\n %s", data[0], {dumps(frame, indent=3)})

    def send_frame(self, data_frame) -> None:
        """Send frame to controller"""

        self.hub_connection.send("SendTo", [self.controller_serial, data_frame])

    def establish_connection(self) -> None:
        """Main function used for connecting with controller and handle callbacks"""

        result = requests.get(
            f"{SERVER_BROKER_URL}/api/connections/broker/whichserver/{self.controller_serial}",
            timeout=5000,
        )

        _LOGGER.info("Entered")

        if result.status_code != 200:
            raise requests.exceptions.ConnectionError

        else:
            _LOGGER.info("Broker address has been acquired!")

            self.server_uri = f"https://{result.text}/broker"

            _LOGGER.info(self.server_uri)

            _LOGGER.info(self.server_uri)

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

        self.hub_connection.on("SendError", _LOGGER.info)
        self.hub_connection.on("Registration", _LOGGER.info)
        self.hub_connection.on("Authorization", self.auth_result)
        self.hub_connection.on("Data", self.data_handler)
        self.hub_connection.on_open(self.start)
        self.hub_connection.start()
