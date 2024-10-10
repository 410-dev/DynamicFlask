import inspect
import hashlib
import json
import os
import shutil

def getConfig(key: str, default = None) -> any:
    with open("config.json", "r") as file:
        data = json.load(file)
        if key not in data:
            return default
        return data[key]

def getInstanceID() -> str:
    # Get path of called script and hash the path
    paths = inspect.stack()
    websiteRoot = getConfig("serverRoot")
    for path in paths:
        newFileName = path.filename.replace("\\", "/")
        if f'{websiteRoot}/' in newFileName:
            instanceName = newFileName.split(f'{websiteRoot}/')[1].split('/')[0]
            if instanceName == newFileName.split(f'{websiteRoot}/')[1]:
                instanceName = "root"
            return instanceName
    print(f"  [WARNING] StorageAPI: Not found in paths. Using auto fallback: {inspect.stack()[1].filename}")

    inspectPath = inspect.stack()[1].filename.replace("\\", "/")
    instanceName = inspectPath.split('/')[-1].split('.')[0]
    return instanceName

def getRawPathToStorage(path: str, createDirectory: bool = True) -> str:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    fullpath = f"{storageLocation}/{instanceId}/{path}"
    if createDirectory:
        parentDir = os.path.dirname(fullpath)
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
    return fullpath

def has(path: str) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    return os.path.exists(f"{storageLocation}/{instanceId}/{path}")

def writeStr(path: str, data: str) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{instanceId}/{path}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{instanceId}/{path}", "w") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to write to {path}: {e}")
        return False

def readStr(path: str) -> str:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    try:
        with open(f"{storageLocation}/{instanceId}/{path}", "r") as file:
            return file.read()

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to read from {path}: {e}")
        return ""

def appendStr(path: str, data: str) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{instanceId}/{path}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{instanceId}/{path}", "a") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to append to {path}: {e}")
        return False

def writeBytes(path: str, data: bytes) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{instanceId}/{path}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{instanceId}/{path}", "wb") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to write to {path}: {e}")
        return False

def readBytes(path: str) -> bytes:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    try:
        with open(f"{storageLocation}/{instanceId}/{path}", "rb") as file:
            return file.read()

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to read from {path}: {e}")
        return b""

def remove(path: str) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("storageDir")
    try:
        if os.path.isdir(f"{storageLocation}/{instanceId}/{path}"):
            shutil.rmtree(f"{storageLocation}/{instanceId}/{path}")
        else:
            os.remove(f"{storageLocation}/{instanceId}/{path}")
        return True
    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to remove {path}: {e}")
        return False

def cacheStr(key: str, data: str) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("cacheDir")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{instanceId}/{key}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{instanceId}/{key}", "w") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to cache {key}: {e}")
        return False

def cacheBytes(key: str, data: bytes) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("cacheDir")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{instanceId}/{key}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{instanceId}/{key}", "wb") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to cache {key}: {e}")
        return False

def readCacheStr(key: str) -> str:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("cacheDir")
    try:
        with open(f"{storageLocation}/{instanceId}/{key}", "r") as file:
            return file.read()

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to read from cache {key}: {e}")
        return ""

def readCacheBytes(key: str) -> bytes:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("cacheDir")
    try:
        with open(f"{storageLocation}/{instanceId}/{key}", "rb") as file:
            return file.read()

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to read from cache {key}: {e}")
        return b""

def removeCache(key: str) -> bool:
    instanceId: str = getInstanceID()
    storageLocation: str = getConfig("cacheDir")
    try:
        if os.path.isdir(f"{storageLocation}/{instanceId}/{key}"):
            shutil.rmtree(f"{storageLocation}/{instanceId}/{key}")
        else:
            os.remove(f"{storageLocation}/{instanceId}/{key}")
        return True
    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to remove cache {key}: {e}")
        return False

def writeSharedStr(path: str, data: str) -> bool:
    storageLocation: str = getConfig("sharedStorage")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{path}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{path}", "w") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to write to {path}: {e}")
        return False

def readSharedStr(path: str) -> str:
    storageLocation: str = getConfig("sharedStorage")
    try:
        with open(f"{storageLocation}/{path}", "r") as file:
            return file.read()

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to read from {path}: {e}")
        return ""

def writeSharedBytes(path: str, data: bytes) -> bool:
    storageLocation: str = getConfig("sharedStorage")
    try:
        parentDir = os.path.dirname(f"{storageLocation}/{path}")
        if not os.path.exists(parentDir):
            os.makedirs(parentDir, exist_ok=True)
        with open(f"{storageLocation}/{path}", "wb") as file:
            file.write(data)
        return True

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to write to {path}: {e}")
        return False

def readSharedBytes(path: str) -> bytes:
    storageLocation: str = getConfig("sharedStorage")
    try:
        with open(f"{storageLocation}/{path}", "rb") as file:
            return file.read()

    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to read from {path}: {e}")
        return b""

def removeShared(path: str) -> bool:
    storageLocation: str = getConfig("sharedStorage")
    try:
        if os.path.isdir(f"{storageLocation}/{path}"):
            shutil.rmtree(f"{storageLocation}/{path}")
        else:
            os.remove(f"{storageLocation}/{path}")
        return True
    except Exception as e:
        print(f"  [WARNING] StorageAPI: Failed to remove {path}: {e}")
        return False

def isInSharedStorage(path: str) -> bool:
    storageLocation: str = getConfig("sharedStorage")
    return os.path.exists(f"{storageLocation}/{path}")
