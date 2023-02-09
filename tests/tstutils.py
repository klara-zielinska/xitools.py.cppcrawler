import os
import shutil


def zipdict_longest(d1, d2):
    res = {}
    for k, v in d1.items():
        res[k] = (v, None)
    for k, v in d2.items():
        res[k] = (res.get(k, (None, None))[0], v)
    return res


def dataFilepath(dataSet, filename=None, *, abs=True):
    if filename: path = f"data/{dataSet}/{filename}"
    else:        path = f"data/{dataSet}"

    if abs: return os.path.abspath(path)
    else:   return os.path.normpath(path)


def tmpFilepath(testSuit, filename=None, *, abs=True):
    if filename: path = f"tmp/{testSuit}/{filename}"
    else:        path = f"tmp/{testSuit}"

    if abs: return os.path.abspath(path)
    else:   return os.path.normpath(path)


def prepareTmpDir(testSuit):
    dir = tmpFilepath(testSuit)
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    return dir


def testMapSMD(fn, smd):
    ssd       = { src.filepath() : list(map(fn, matches)) for src, matches in smd.items() if src }
    if None in smd:
        ssd[None] = { src.filepath() : list(map(fn, matches)) for src, matches in smd[None].items() }
    return ssd