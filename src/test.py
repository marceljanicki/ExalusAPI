import dataclasses, json, time, uuid

from main import Pyexalus, DataFrame, Method, Status

conn = Pyexalus("QT54K96X3P", 9299, "installator@installator", "QT54K96X3P9299")

conn.establish_connection()

time.sleep(0.5)

conn.send_frame(
    json.dumps(
        dataclasses.asdict(
            DataFrame(
                "/devices/device/control",
                Status.OK.value,
                Method.Post.value,
                str(uuid.uuid1()),
                {
                    "DeviceGuid": "2e0a79c9-175b-49b1-980b-65a35c715000",
                    "Channel": 1,
                    "ControlFeature": 0,
                },
            )
        )
    )
)


while True:

    pass

