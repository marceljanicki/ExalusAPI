import dataclasses
import json
import uuid
import exalusAPI

conn = exalusAPI.Controller("QT54K96X3P", 9299, "installator@installator", "QT54K96X3P9299")

conn.establish_connection()

conn.send_frame(
    json.dumps(
        dataclasses.asdict(
            exalusAPI.DataFrame(
                "/devices/device/control",
                exalusAPI.Status.OK.value,
                exalusAPI.Method.Post.value,
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