import os
import shutil


def zipdict_longest(d1, d2):
    res = {}
    for k, v in d1.items():
        res[k] = (v, None)
    for k, v in d2.items():
        res[k] = (res.get(k, (None, None))[0], v)
    return res


def dataFilepath(dataSet, filename):
    return f"data/{dataSet}/{filename}"


def tmpFilepath(testSuit, filename=None):
    if filename:
        return f"tmp/{testSuit}/{filename}"
    else:
        return f"tmp/{testSuit}"


def prepareTmpDir(testSuit):
    dir = tmpFilepath(testSuit)
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)