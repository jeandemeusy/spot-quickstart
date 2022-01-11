import sys
import enum
import argparse
import bosdyn.client.util

from robot import Robot


class ExecutionType(enum.Enum):
    MOVE = 0
    IMAGES = 1
    ELSE = 2


execution = ExecutionType.MOVE
cameras = [
    "frontleft",
    "frontright",
    "left",
    "right",
    "back",
]
sources = [
    "back_depth",
    "back_depth_in_visual_frame",
    "back_fisheye_image",
    "frontleft_depth",
    "frontleft_depth_in_visual_frame",
    "frontleft_fisheye_image",
    "frontright_depth",
    "frontright_depth_in_visual_frame",
    "frontright_fisheye_image",
    "left_depth",
    "left_depth_in_visual_frame",
    "left_fisheye_image",
    "right_depth",
    "right_depth_in_visual_frame",
    "right_fisheye_image",
]


def jdu_spot(config):
    spot = Robot("JDUSpotClient", config.hostname, config.verbose)
    spot.authenticate(config.username, config.password)

    spot.assertIsNotEStop()
    spot.getLease()

    try:
        with spot.leaseKeepAlive():
            if execution == ExecutionType.MOVE:
                spot.powerOn()
                spot.standUp(sleepSec=0.2)

                spot.twistPosition(25, 0, 0, sleepSec=1)
                spot.twistPosition(25, 0, 0, sleepSec=1)
                spot.standTaller(height=0.1, sleepSec=0.5)

                spot.move(0.5, 0, 0)
                spot.move(-0.5, 0, 0)

                spot.powerOff(cutImmediately=False)
                spot.logComment("JDU movement finished.")

            elif execution == ExecutionType.IMAGES:
                spot.powerOn()
                spot.standUp(sleepSec=0.2)

                if config.source:
                    spot.getImage(
                        config.source,
                        path="results/from_source",
                        name=f"jdu_{config.source}.png",
                    )

                if config.camera == "all":
                    for camera in cameras:
                        spot.getDepthBlend(
                            camera,
                            path="results/depth_images",
                            name=f"jdu_{camera}.png",
                        )
                if config.camera in cameras:
                    spot.getDepthBlend(
                        config.camera,
                        path="results/depth_images",
                        name=f"jdu_{config.camera}.png",
                    )

                spot.powerOff(cutImmediately=False)

                spot.logComment("JDU camera finished.")
            elif execution == ExecutionType.ELSE:
                pass
    finally:
        spot.returnLease()


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument(
        "--source",
        default="back_fisheye_image",
        help="Set the target camera.",
    )
    parser.add_argument(
        "--camera",
        default="back",
        help="Blend visual frame and depth images.",
    )

    options = parser.parse_args(argv)
    try:
        jdu_spot(options)
        return True
    except Exception as exc:
        logger = bosdyn.client.util.get_logger()
        logger.error("Hello, Spot! threw an exception: %r", exc)
        return False


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
