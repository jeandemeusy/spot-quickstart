import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client import math_helpers
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.frame_helpers import (
    ODOM_FRAME_NAME,
    BODY_FRAME_NAME,
    get_se2_a_tform_b,
)
from bosdyn.client.robot_command import (
    RobotCommandBuilder,
    RobotCommandClient,
    blocking_stand,
)
import bosdyn.geometry

from bosdyn.client.image import ImageClient
from bosdyn.api import image_pb2
from bosdyn.api.basic_command_pb2 import RobotCommandFeedbackStatus

import time
import math
from pathlib import Path
import numpy as np
import cv2 as cv
from scipy import ndimage


class Robot:
    """BostonDynamics Spot robot abstraction class."""

    def __init__(self, clientname: str, hostname: str, verbose: bool = True):
        """
        Initialisation of the robot.

        Parameters
        ----------
        clientname: str
            User-purpose name of the client.
        hostname: str
            Hostname or address of robot, e.g. "beta25-p" or "192.168.80.3".
        verbose: bool (optional)
            Print debug-level messages (default is True)
        """

        bosdyn.client.util.setup_logging(verbose)

        self.sdk = bosdyn.client.create_standard_sdk(clientname)
        self.hostname = hostname
        self.robot = self.sdk.create_robot(self.hostname)
        self.camera_angles = {
            "back": 0,
            "frontleft": -78,
            "frontright": -102,
            "left": 0,
            "right": 180,
        }

    def authenticate(self, username: str, password: str):
        """
        Authenticates the user on the robot.

        Parameters
        ----------
        username: str
            User name of account to get credentials for.
        password: str
            Password to get credentuials for.
        """

        self.robot.authenticate(username, password)
        self.robot.time_sync.wait_for_sync()

    def assertIsNotEStop(self):
        """Asserts that the robot is not e-steopped."""

        assert not self.robot.is_estopped(), (
            "Robot is estopped. Please use an external E-Stop client, "
            "such as the estop SDK example, to configure E-Stop."
        )

    def getLease(self):
        """Takes or acquires the lease on the robot. Only one actor can take control of the robot at a time, this function ensures that we have the control."""

        self.lease_client = self.robot.ensure_client(
            bosdyn.client.lease.LeaseClient.default_service_name
        )
        self.lease = self.lease_client.take()

    def leaseKeepAlive(self):
        """Issues lease liveness choecks on a background thread."""

        return bosdyn.client.lease.LeaseKeepAlive(self.lease_client)

    def returnLease(self):
        """Returns leases so that someone else can take control of the robot."""

        self.lease_client.return_lease(self.lease)

    def powerOn(self):
        """Safely powers-on the robot, and gets all necessary clients for the robot to work properly (command, state and image clients)."""

        self.robot.logger.info("Powering on robot... This may take several seconds.")
        self.robot.power_on(timeout_sec=20)

        assert self.robot.is_powered_on(), "Robot power on failed."

        self.robot.logger.info("Robot powered on.")

        self.getClients()

    def powerOff(self, cutImmediately: bool = False, timeoutSec: int = 20):
        """Safely powers-off the robot.

        Parameters
        ----------
        cutImmediately: bool (optional)
            Force shutdown the robot in the current position. Not Safe. (default is False)
        timeoutSec: int (optional)
            Shutdown timeout in seconds. (default is 20)
        """

        self.robot.power_off(
            cut_immediately=cutImmediately,
            timeout_sec=timeoutSec,
        )
        assert not self.robot.is_powered_on(), "Robot power off failed."
        self.robot.logger.info("Robot safely powered off.")

    def getClients(self):
        """Gets all necessary clients for the robot to work properly (command, state and image clients)."""

        self.command_client = self.robot.ensure_client(
            RobotCommandClient.default_service_name,
        )
        self.state_client = self.robot.ensure_client(
            RobotStateClient.default_service_name,
        )
        self.image_client = self.robot.ensure_client(
            ImageClient.default_service_name,
        )

        self.robot.logger.info("Robot clients available.")

    def standUp(self, sleepSec: int, timeoutSec: int = 10):
        """Makes the robot standing up.

        Parameters
        ----------
        sleepSec: int
            Waiting time after the command is complete in seconds.
        timoutSec: int (optional)
            Command timeout in seconds. (default is 10)
        """
        self.robot.logger.info("Commanding robot to stand...")

        blocking_stand(self.command_client, timeout_sec=timeoutSec)

        self.robot.logger.info("Robot standing.")

        time.sleep(sleepSec)

    def twistPosition(self, yaw: float, roll: float, pitch: float, sleepSec: int):
        """Twists the robot staying at the same place.

        Parameters
        ----------
        yaw: float
            yaw angle in degrees
        roll: float
            roll angle in degrees
        pitch: float
            pitch angle in degrees
        sleepSec: int
            Waiting time after the command is complete in seconds.
        """

        pose = bosdyn.geometry.EulerZXY(
            yaw=math.radians(yaw),
            roll=math.radians(roll),
            pitch=math.radians(pitch),
        )
        cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=pose)
        self.command_client.robot_command(cmd)
        self.robot.logger.info("Robot standing twisted.")
        time.sleep(sleepSec)

    def standTaller(self, height: float, sleepSec: int):
        """Changes robot's body height.

        Parameters
        ----------
        height: float
            Height to stand at relative to a nominal stand height, in meters.
        sleepSec: int
            Waiting time after the command is complete in seconds.
        """

        cmd = RobotCommandBuilder.synchro_stand_command(body_height=height)
        self.command_client.robot_command(cmd)
        self.robot.logger.info("Robot standing tall.")
        time.sleep(sleepSec)

    def move(
        self,
        dx: float,
        dy: float,
        dyaw: float,
        frame_name=ODOM_FRAME_NAME,
        stairs=False,
    ):
        """Makes a relative movement from its current position.

        Parameters
        ----------
        dx: float
            x-direction distance to go to, in meters.
        dy: float
            y-direction distance to go to, in meters.
        dyaw: float
            z-axis rotation angle, in degrees.
        frame_name: str (optional)
            Output frame, either odom or vision frame. (default is ODOM_FRAME_NAME)
        stairs: bool (optional)
            Stairs mode. (default is False)
        """

        transforms = (
            self.state_client.get_robot_state().kinematic_state.transforms_snapshot
        )

        bodyTFormGoal = math_helpers.SE2Pose(x=dx, y=dy, angle=math.radians(dyaw))
        outTFormGoal = get_se2_a_tform_b(transforms, frame_name, BODY_FRAME_NAME)
        outTFormGoal = outTFormGoal * bodyTFormGoal

        robot_cmd = RobotCommandBuilder.synchro_se2_trajectory_point_command(
            goal_x=outTFormGoal.x,
            goal_y=outTFormGoal.y,
            goal_heading=outTFormGoal.angle,
            frame_name=frame_name,
            params=RobotCommandBuilder.mobility_params(stair_hint=stairs),
        )
        end_time = 10.0
        cmd_id = self.command_client.robot_command(
            lease=None, command=robot_cmd, end_time_secs=time.time() + end_time
        )
        self.robot.logger.info("Robot moving.")

        # Wait until the robot has reached the goal.
        while True:
            feedback = self.command_client.robot_command_feedback(cmd_id)
            mobility_feedback = (
                feedback.feedback.synchronized_feedback.mobility_command_feedback
            )
            if mobility_feedback.status != RobotCommandFeedbackStatus.STATUS_PROCESSING:
                print("Failed to reach the goal")
                return False
            traj_feedback = mobility_feedback.se2_trajectory_feedback
            if (
                traj_feedback.status == traj_feedback.STATUS_AT_GOAL
                and traj_feedback.body_movement_status
                == traj_feedback.BODY_STATUS_SETTLED
            ):
                print("Arrived at the goal.")
                return True
            time.sleep(0.5)

    def getImage(self, source: str, path: str = None, name: str = None):
        """Acquires an image and saves it.

        Parameters
        ----------
        source: str
            Name of the camera to use (e.g. "frontleft_fisheye_image").
        path: str or Any (optional)
            Destination folder. If it doesn't exist, it will be created on runtime. (default is None)
        name: str or Any (optional)
            File name. (default is None).
        """

        image_response = self.image_client.get_image_from_sources([source])
        image = image_response[0].shot.image
        key = source.split("_")[0]

        try:
            if "depth" in source:
                image = self._convertDepthToImage(image)
            else:
                image = self._convertVisualToImage(image)
        except Exception as exc:
            self.robot.logger.warning(
                "Exception thrown while converting image. %r", exc
            )

        image = ndimage.rotate(image, self.camera_angles[key])
        name = self.getFullPath(path, name)
        self.saveImage(name, image)

    def getDepthBlend(self, camera: str, path: str = None, name: str = None):
        """Blends visual frame and depth informations in an unique image.

        Parameters
        ----------
        camera: str
            Name of the camera to use given by it's position ("frontleft", "frontright", "left", "right" or "back").
        path: str or Any (optional)
            Destination folder. If it doesn't exist, it will be created on runtime. (default is None)
        name: str or Any (optional)
            File name. (default is None).
        """

        sources = [camera + "_depth_in_visual_frame", camera + "_fisheye_image"]
        image_responses = self.image_client.get_image_from_sources(sources)

        depth = self._convertDepthToImage(image_responses[0].shot.image)
        visual = self._convertVisualToImage(image_responses[1].shot.image)
        self.robot.logger.info("Both images captured and transformed")

        visual_rgb = (
            cv.cvtColor(cv.cvtColor(visual, cv.COLOR_RGB2GRAY), cv.COLOR_GRAY2RGB)
            if len(visual.shape) == 3
            else cv.cvtColor(visual, cv.COLOR_GRAY2RGB)
        )

        image = cv.addWeighted(visual_rgb, 0.5, depth, 0.5, 0)
        image = ndimage.rotate(image, self.camera_angles[camera])

        name = self.getFullPath(path, name)
        self.saveImage(name, image)

    def getFullPath(self, path: str, name: str):
        """Creates full paths from folder and file name.

        Parameters
        ----------
        path: str
            Destination folder. If it doesn't exist, it will be created on runtime.
        name: str
            File name.
        """

        if path is not None:
            path: Path = Path(path)
            if not path.exists():
                path.mkdir(parents=True)

            name = str(path.cwd().joinpath(path, name).resolve())
            self.robot.logger.info("Saving image to: {}".format(name))
        else:
            self.robot.logger.info(
                "Saving image to working directory as {}".format(name)
            )

        return name

    def saveImage(self, fullpath: str, image: np.ndarray):
        """Saves an image.

        Parameters
        ----------
        fullpath: str
            Complete path (folder + filename) of the new image.
        image: ndarray
            Image to save.
        """

        try:
            cv.imwrite(fullpath, image)
        except Exception as exc:
            self.robot.logger.warning("Exception thrown saving image. %r", exc)

    def logComment(self, comment: str):
        """Creates comment in the robot's log.

        Parameters
        ----------
        comment: str
            Comment to write in the robot's log.
        """

        self.robot.operator_comment(comment)
        self.robot.logger.info('Added comment "%s" to robot log.', comment)

    def _convertVisualToImage(self, image):
        """Convert robot visual image to a numpy array.

        Parameters
        ----------
        image: Any
            Robot's visual image.
        """

        if image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
            num_bytes = 1
            dtype = np.uint16
        elif image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
            num_bytes = 3
            dtype = np.uint8
        elif image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGBA_U8:
            num_bytes = 4
            dtype = np.uint8
        elif image.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
            num_bytes = 1
            dtype = np.uint8
        elif image.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U16:
            num_bytes = 2
            dtype = np.uint8

        img = np.frombuffer(image.data, dtype=dtype)
        if image.format == image_pb2.Image.FORMAT_RAW:
            try:
                img = img.reshape((image.rows, image.cols, num_bytes))
            except ValueError:
                img = cv.imdecode(img, -1)
        else:
            img = cv.imdecode(img, -1)

        return img

    def _convertDepthToImage(self, image):
        """Convert robot depth image to a numpy array.

        Parameters
        ----------
        image: Any
            Robot's visual image.
        """

        cv_depth = np.frombuffer(image.data, dtype=np.uint16)
        cv_depth = cv_depth.reshape(image.rows, image.cols)

        min_val = np.min(cv_depth)
        max_val = np.max(cv_depth)
        depth_range = max_val - min_val
        depth8 = (255.0 / depth_range * (cv_depth - min_val)).astype("uint8")
        depth8_rgb = cv.cvtColor(depth8, cv.COLOR_GRAY2RGB)
        depth_color = cv.applyColorMap(depth8_rgb, cv.COLORMAP_JET)

        return depth_color
