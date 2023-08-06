import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()) + "/pialert/")


import datetime

from helper import timeNowTZ, updateSubnets


# -------------------------------------------------------------------------------
def test_helper():
    assert timeNow() == datetime.datetime.now().replace(microsecond=0)


# -------------------------------------------------------------------------------
def test_updateSubnets():
    # test single subnet
    subnet = "192.168.1.0/24 --interface=eth0"
    result = updateSubnets(subnet)
    assert type(result) is list
    assert len(result) == 1

    # test multip subnets
    subnet = ["192.168.1.0/24 --interface=eth0", "192.168.2.0/24 --interface=eth1"]
    result = updateSubnets(subnet)
    assert type(result) is list
    assert len(result) == 2
