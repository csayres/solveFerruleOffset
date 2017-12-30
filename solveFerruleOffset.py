import os
import glob
import pickle
from astropy.io import fits
import subprocess
import numpy
import datetime
from multiprocessing import Pool

GCAM_PATH = "/uufs/chpc.utah.edu/common/home/sdss/sdsswork/lco/gcam"

# based on this threshold we can decide weather or not we're
# relatively centered on field
GDRMS_THRESH = 0.6

# phi = the rotation of the alignment pin measured North to East, in degrees

# rotStar2Sky = Rotation of a guide fiber image on the guide camera (measured
# counter  clockwise from the guider x axis North). Rotation of the guide
# fiber image  by -rotStar2Sky produces a North up image.

# rotStar2Sky = 90 + fiber rotation - phi
class ProcGimg(object):
    def __init__(self, fitsFilePath):
        with fits.open(fitsFilePath) as f:
            self.grms = f[0].header["GDRMS"]
            self.cartID = f[0].header["CARTID"]
            self.plateID = f[0].header["PLATEID"]
            self.seeing = f[0].header["SEEING"]
            self.offRA = f[0].header["DRA"]
            self.offDec = f[0].header["DDEC"]
            self.offRot = f[0].header["DROT"]
            self.offFocus = f[0].header["DFOCUS"]
            self.offScale = f[0].header["DSCALE"]
            self.xFocal = f[-1].data["xFocal"]
            self.yFocal = f[-1].data["yFocal"]
            self.rotation = f[-1].data["rotation"]
            self.phi = f[-1].data["phi"]
            self.rotStar2Sky = f[-1].data["rotStar2Sky"]
            self.xCenter = f[-1].data["xCenter"]
            self.yCenter = f[-1].data["yCenter"]
            self.xstar = f[-1].data["xstar"]
            self.ystar = f[-1].data["ystar"]
            self.dx = f[-1].data["dx"]
            self.dy = f[-1].data["dy"]
            self.dRA = f[-1].data["dRA"]
            self.dDec = f[-1].data["dDec"]
            # parse date as datetime
            dt = f[0].header["DATE-OBS"]
            dt = dt.split(".")[0]
            self.dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            # parse mjd dir and expno
            filename = f[0].header["FILENAME"]
            self.mjd = int(filename.split("/data/gcam/")[-1].split("/")[0])
            self.expno = int(filename.split("gimg-")[-1].split(".")[0])

def compileGCAM(gcamPath):
    procList = []
    for d, _, files in os.walk(gcamPath):
        for file in files:
            if not file.startswith("proc-"):
                pass
            filename = os.path.join(d, file)
            try:
                procGimg = ProcGimg(filename)
            except:
                continue
            procList.append(procGimg)
    return procList

def getProcPaths(gcamPath, minMJD = None):
    keepMJDs = []
    allMJDs = glob.glob(os.path.join(gcamPath, "*"))
    if minMJD is not None:
        for mjd in allMJDs:
            if int(os.path.split(mjd)[-1]) < minMJD:
                continue
            keepMJDs.append(mjd)
    else:
        keepMJDs = allMJDs
    allProcFiles = []
    for mjd in keepMJDs:
        procList = glob.glob(os.path.join(mjd, "proc-*"))
        allProcFiles.extend(procList)
    return allProcFiles


def sortProcList(procList):
    outDict = {}
    for proc in procList:
        if proc.grms > GDRMS_THRESH:
            continue
        if numpy.isnan(proc.xCenter[-1]):
            continue # no LED measurement
        if proc.cartID not in outDict:
            outDict[proc.cartID] = {}
        if proc.plateID not in outDict[proc.cartID]:
            outDict[proc.cartID][proc.plateID] = []
        outDict[proc.cartID][proc.plateID].append(proc)
    return outDict

def processGimg(gimgPath):
    try:
        return ProcGimg(gimgPath)
    except:
        return None

procFileList = getProcPaths(GCAM_PATH, minMJD = 58090)
p = Pool(20)
print("start multiprocessing")
procListWithNones = p.map(processGimg, procFileList)
print("done multiprocessing")
# remove Nones from procList:
procList = [x for x in procListWithNones if x is not None]
outDict = sortProcList(procList)
import pdb; pdb.set_trace()




