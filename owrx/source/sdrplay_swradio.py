from owrx.command import Option
from .direct import DirectSource
from subprocess import Popen

import logging

logger = logging.getLogger(__name__)


class SdrplaySwradioSource(DirectSource):
    def getCommandMapper(self):
        return (
                super().getCommandMapper()
                    .setBase("./swradio.sh")
                    .setMappings({
                        "device": Option("-D"),
                        "samp_rate": Option("-s"),
                        "center_freq": Option("-f"),
                        "rf_gain": Option("-g")}
                    )
                    #.setStatic("-t raw -f S16_LE -c2 -")
            )

    def getEventNames(self):
        return super().getEventNames() + ["device"]

    def getFormatConversion(self):
        return ["csdr convert_s16_f"]
        #return ["csdr convert_s16_f", "csdr gain_ff 5"]

    def updateParams(self, frequency=None, rf_gain=None, samp_rate=None):
        cmd = ["./swradio_update.sh"]
        if frequency:
            cmd += ["-f", f"{int(frequency):d}"]
        if rf_gain:
            cmd += ["-g", f"{int(rf_gain):d}"]
        if samp_rate:
            cmd += ["-s", f"{int(samp_rate):d}"]

        process = Popen(cmd)
        process.communicate()
        rc = process.wait()
        if rc != 0:
            logger.warning("parameter change failed; rc=%i", rc)

    def preStart(self):
        values = self.getCommandValues()
        self.updateParams(frequency=values["center_freq"])

    def onPropertyChange(self, name, value):
        if name == "center_freq":
            self.updateParams(frequency=value)
        elif name == "rf_gain":
            self.updateParams(rf_gain=value)
        elif name == "samp_rate":
            self.updateParams(samp_rate=value)
