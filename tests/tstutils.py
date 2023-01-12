import os
import shutil


def zipdict_longest(d1, d2):
    res = {}
    for k, v in d1.items():
        res[k] = (v, None)
    for k, v in d2.items():
        res[k] = (res.get(k, (None, None))[0], v)
    return res


def dataFilepath(dataSet, filename=None):
    if filename:
        return os.path.abspath(f"data/{dataSet}/{filename}")
    else:
        return os.path.abspath(f"data/{dataSet}")


def tmpFilepath(testSuit, filename=None):
    if filename:
        return os.path.abspath(f"tmp/{testSuit}/{filename}")
    else:
        return os.path.abspath(f"tmp/{testSuit}")


def prepareTmpDir(testSuit):
    dir = tmpFilepath(testSuit)
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    return dir