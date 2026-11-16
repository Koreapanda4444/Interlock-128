import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from common import BudgetExceeded, Deadline, Driver, ResearchFailure, research_key, stream


def main(driver):
    direct = b"Interlock-128/research\0discovery\0" + struct.pack("<IIII",20261109,4,31,0)
    import hashlib
    assert stream("discovery",4,31,0,64) == hashlib.shake_256(direct).digest(64)
    assert research_key(0) == stream("key",0,0,0,32)
    try:
        Deadline(0).check()
    except BudgetExceeded:
        pass
    else:
        raise AssertionError("zero budget did not expire")
    try:
        Driver(driver,Deadline(10)).raw("invalid\n")
    except ResearchFailure:
        pass
    else:
        raise AssertionError("driver failure was accepted")
    try:
        Driver([sys.executable,"-c","import time; time.sleep(1)"],Deadline(0.02)).raw("")
    except BudgetExceeded:
        pass
    else:
        raise AssertionError("driver timeout was not classified")
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder)/"incomplete.json"
        result = subprocess.run([sys.executable,str(Path(__file__).with_name("run.py")),
                                 "--driver",str(driver),"--output",str(output),"--budget-seconds","0"],
                                capture_output=True,text=True,timeout=10,check=False)
        report = json.loads(output.read_text())
        assert result.returncode == 2 and report["status"] == "incomplete"
        assert "error" not in report and report["provenance"]["driver_sha256"]
        result = subprocess.run([sys.executable,str(Path(__file__).with_name("run.py")),
                                 "--driver",str(Path(folder)/"missing-driver"),"--output",str(output)],
                                capture_output=True,text=True,timeout=10,check=False)
        report = json.loads(output.read_text())
        assert result.returncode == 1 and report["status"] == "failed" and report["phase"] == "initialization"
    print("research framing, reproducibility, failure, timeout and incomplete checkpoint passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver",type=Path,required=True)
    main(parser.parse_args().driver)
