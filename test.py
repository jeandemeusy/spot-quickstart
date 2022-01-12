import enum
import inspect


class CameraType(enum.Enum):
    FRONTLEFT = "frontleft"
    FRONTRIGHT = "frontright"
    LEFT = "left"
    RIGHT = "right"
    BACK = "back"

    @classmethod
    def values(self):
        return [item.value for item in self]


class CameraSource:
    class Back(enum.Enum):
        DEPTH = "back_depth"
        DEPTH_VISUAL_FRAME = "back_depth_in_visual_frame"
        FISHEYE = "back_fisheye_image"

    class FrontLeft(enum.Enum):
        DEPTH = "frontleft_depth"
        DEPTH_VISUAL_FRAME = "frontleft_depth_in_visual_frame"
        FISHEYE = "frontleft_fisheye_image"

    class FrontRight(enum.Enum):
        DEPTH = "frontright_depth"
        DEPTH_VISUAL_FRAME = "frontright_depth_in_visual_frame"
        FISHEYE = "frontright_fisheye_image"

    class Left(enum.Enum):
        DEPTH = "left_depth"
        DEPTH_VISUAL_FRAME = "left_depth_in_visual_frame"
        FISHEYE = "left_fisheye_image"

    class Right(enum.Enum):
        DEPTH = "right_depth"
        DEPTH_VISUAL_FRAME = "right_depth_in_visual_frame"
        FISHEYE = "right_fisheye_image"

    @classmethod
    def values(self):
        enums = [cls for cls in self.__dict__.values() if inspect.isclass(cls)]
        return [item.value for sub in enums for item in sub]


def main():

    print(f"{CameraSource.values()=}")

    condition = None in CameraSource.values()
    print(f"{condition=}")


if __name__ == "__main__":
    main()
