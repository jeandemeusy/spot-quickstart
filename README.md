# Spot Quickstart

This guide will help you set up your programming environment to successfully command and control Boston Dynamics' `Spot` robot using the `Spot Python SDK`. The guide defaults to a Linux setup.

**Windows users:** Please find notes like this to help you where Windows may differ from Linux.

* [System Setup](#system-setup)
    * [System Requirements](#system-requirements)
    * [Python Requirements](#python-requirements)
    * [Pip Installation](#pip-installation)
* [Install Spot Python Packages](#install-spot-python-packages)
    * [Verify your Spot packages installation](#verify-your-spot-packages-installation)
* [Verify you can command and query Spot](#verify-you-can-command-and-query-spot)
    * [Get a user account on the robot](#get-a-user-account-on-the-robot)
    * [Ping Spot](#ping-spot)
    * [Request Spot robot's ID](#request-spot-robots-id)
* [Run an example code](#run-an-example-code)
    * [Run an Independent E-Stop](#run-an-independent-e-stop)
    * [Run the main](#run-the-main)
* [Documentation](#documentation)

## System setup

### System requirements

The Boston Dynamics Spot Python SDK works with most operating systems including:
* Linux Ubuntu 18.04 LTS
* Windows 10
* MacOS 10.14 (Mojave)

Windows WSL use is discouraged due to so many examples having graphics.

### Python requirements

Spot Python SDK works with Python 3.6 to 3.9.
The example code below has been tested with Python 3.9.4. All library requirements conforms to this python version.

Downloads and instructions for installing Python can be found at https://www.python.org/.

**We use "python" in this guide but**...if you have multiple versions of Python installed then running `python` might reference an incorrect version (e.g. version 2.7).  For example, to run python 3 on Ubuntu 18.04 you would run `python3` and on Windows you could use the [Python launcher](https://docs.python.org/3/using/windows.html#launcher) and run `py -3`. Our documentation uses `python` assuming that the command launches a compatible version of Python.  `Virtualenv` (described below), is an excellent way to resolve these issues.

Verify your python install is the correct version.  Open a command prompt or start your python IDE:
```
$ python --version
Python 3.6.8
```

### Pip Installation

Pip is the package installer for Python. The Spot SDK and the third-party packages used by many of its programming examples use pip to install.

Check if pip is installed by requesting its version:

```
$ pip --version
pip 19.2.1 from <PATH_ON_YOUR_COMPUTER>
```

**Windows users:**

```shell
> pip --version
```

If pip is not found, you'll need to install it. There are a few options:

  * pip comes preinstalled with all Python 3 versions >= 3.4 downloaded from python.org
  * Use the [`get-pip.py` installation script.](https://pip.pypa.io/en/stable/installing/)
  * Use an OS-specific package manager (such as the python3-pip package on Ubuntu)


**Permission Denied:** If you do not use virtualenv (described below), when you install packages using pip, you may receive Permission Denied errors, if so, add the `--user` option to your pip command.

## Install Spot Python packages

With `python` and `pip` properly installed and configured, the Python packages are easily installed
or upgraded from PyPI with the following command.

```shell
$ pip install -r requirements.txt
```

**Version incompatibility:**

If you see a version incompatibility error during pip install such as:

```shell
ERROR: bosdyn-core <VERSION_STRING> has requirement bosdyn-api==<VERSION_STRING>, but you
have bosdyn-api 3.0.3 which is incompatible.
```

Try uninstalling the bosdyn packages (Note: unlike install, you will need to explicitly list all 4 packages) and then reinstalling:

```shell
$ pip uninstall bosdyn-client bosdyn-mission bosdyn-api bosdyn-core
$ pip install bosdyn-client bosdyn-mission
```

### Verify your Spot packages installation
Make sure that the packages have been installed.

```shell
$ pip list --format=columns | grep bosdyn
bosdyn-api                    3.0.3
bosdyn-choreography-client    3.0.3
bosdyn-choreography-protos    3.0.3
bosdyn-client                 3.0.3
bosdyn-core                   3.0.3
bosdyn-mission                3.0.3
```
**Windows users:**
```shell
> pip list --format=columns | findstr bosdyn
```

If you don't see the 4 bosdyn packages with your target version, something went wrong during
installation.  Contact support@bostondynamics.com for help.

Next, start the python interpreter:

```shell
$ python3
Python 3.6.8 (default, Jan 6 2022, 11:02:34)
[GCC 8.0.1 20180414 (experimental) [trunk revision 259383]] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import bosdyn.client
>>> help(bosdyn.client)
Help on package bosdyn.client in bosdyn:

NAME
    bosdyn.client

DESCRIPTION
    The client library package.
    Sets up some convenience imports for commonly used classes.

PACKAGE CONTENTS
    __main__
...
```
If the packages are **not** installed correctly, you may see an error like this one:

```python
>>> import bosdyn.client
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'bosdyn.client'
```

If that's the case, run `pip list` again to make sure that the Boston Dynamics Python packages are installed.

If you can't import bosdyn.client without an error, you may have multiple instances of Python on your computer and have installed bosdyn to one while running the other.  Check the pathnames of your python executables. Are they where you'd expect them to be?  If not, this is a potential sign that you may have multiple python installs.  Consider using virtual environments (see above).  If all else fails, contact support@bostondynamics.com for help.

## Verify you can command and query Spot

To verify your packages work correctly with Spot, you need:

*  A Spot robot on the same version as your packages,
*  A user account on the robot

### Get a user account on the robot

If you just unboxed your Spot robot, you will find a sticker inside the battery cavity with wifi, admin, and username "user" credentials.  Please note however that Boston Dynamics recommends that you first have your designated robot administrator log onto the robot with admin credentials and change passwords to increase security.

NOTE: The following examples will assume username "user" and password "password."

### Ping Spot

1. Power on Spot by holding the power button down until the fans start.  Wait for the fans to turn off (and maybe 10-20 seconds after that)
2. Connect to Spot via wifi.
3. Ping spot at 192.168.80.3


```shell
$ ping 192.168.80.3
```

### Request Spot robot's ID

Issue the following command to get your Spot robot's ID:

```shell
$ python3 -m bosdyn.client 192.168.80.3 id
beta-BD-90490007     02-19904-9903   beta29     spot (V3)
Software: 2.3.4 (b11205d698e 2020-12-11 11:53:12)
Installed: 2020-12-11 15:06:57
```

If this worked for you, SUCCESS!  You are now successfully communicating with Spot via Python!  Note that the output returned shows your Spot robot's unique serial number, its nickname and robot type (Boston Dynamics has multiple robots), the software version, and install date.

If you see one of the following:

```shell
$ python3 -m bosdyn.client 192.168.80.3 id
Could not contact robot with hostname "192.168.80.3"
```
```shell
$ python3 -m bosdyn.client 192.168.80.3 id
RetryableUnavailableError: _InactiveRpcError: gRPC service unavailable. Likely transient and can be resolved by retrying the request.
```

The robot is not powered on or is unreachable.  Go back and try to get your ping to work.  You can also try the `-v` or `--verbose` to get more information to debug the issue.

### Run an example code

#### Run an independent E-Stop

Change your working directory to the E-Stop example and run the gui version:


```shell
$ python src/estop/estop_gui.py --username user --password password 192.168.80.3
```

You should now have a big red STOP button displayed on your screen. You're now ready to go! (or stop in an emergency!!)

#### Run the main
OK, now we have an E-Stop. Leave it running, and open a second python window, and run main:

```shell
$ python src/main.py --username user --password password 192.168.80.3
```

Your Spot robot should have powered up its motors, stood up, made a few poses, walked forword 50cm, backward 50cm, and sat down.  If it didn't, be sure to check that the **Motor power enable** button on the back of Spot was properly turned on.

Try it again, and this time, push the E-Stop button and watch the robot do a "glide-stop."  Remember, E-Stop is your friend.

To see an example of what the robot images looks like, change the execution type `MOVE` (in main.py) to  `IMAGES`. Run again the main. This time the robot shoul have stood up, taken a few pictures, and sat down. The taken pictures will be stored in folder called "results".

**Congratulations, you are now a full-fledged Spot Programming Example Operator!**


## Documentation

The Spot SDK documentation is available at https://dev.bostondynamics.com

The Spot Python SDK distribution is available at https://github.com/boston-dynamics/spot-sdk.
