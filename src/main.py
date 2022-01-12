import sys, argparse
import bosdyn.client.util

from robot import Robot
from enums import CameraPosition, CameraSource, ExecutionType


def move_execution(spot: Robot, config):
    spot.powerOn()
    spot.standUp(sleepSec=0.2)

    spot.twistPosition(25, 0, 0, sleepSec=1)
    spot.twistPosition(25, 0, 0, sleepSec=1)
    spot.standTaller(height=0.1, sleepSec=0.5)

    spot.move(0.5, 0, 0)
    spot.move(-0.5, 0, 0)

    spot.powerOff(cutImmediately=False)
    spot.logComment("JDU movement finished.")


def image_execution(spot: Robot, config):
    spot.powerOn()
    spot.standUp(sleepSec=0.2)

    if config.source in CameraSource.values():
        spot.getImage(
            config.source,
            path="results/from_source",
            name=f"jdu_{config.source}.png",
        )

    if config.camera == "all":
        for camera in CameraPosition.values():
            spot.getDepthBlend(
                camera,
                path="results/depth_images",
                name=f"jdu_{camera}.png",
            )
    if config.camera in CameraPosition.values():
        spot.getDepthBlend(
            config.camera,
            path="results/depth_images",
            name=f"jdu_{config.camera}.png",
        )

    spot.powerOff(cutImmediately=False)

    spot.logComment("JDU camera finished.")


def else_execution(spot: Robot, config):
    pass


def jdu_spot(config, exec: ExecutionType = ExecutionType.ELSE):
    spot = Robot("JDUSpotClient", config.hostname, config.verbose)
    spot.authenticate(config.username, config.password)

    spot.assertIsNotEStop()
    spot.getLease()

    try:
        with spot.leaseKeepAlive():
            if exec == ExecutionType.MOVE:
                move_execution(spot, config)
            elif exec == ExecutionType.IMAGES:
                image_execution(spot, config)
            elif exec == ExecutionType.ELSE:
                else_execution(spot, config)
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
        jdu_spot(options, ExecutionType.MOVE)
        return True
    except Exception as exc:
        logger = bosdyn.client.util.get_logger()
        logger.error("Hello, Spot! threw an exception: %r", exc)
        return False


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
