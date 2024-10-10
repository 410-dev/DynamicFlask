import storageapi
import os
import json

def API_DECLARE() -> dict[str, str]:
    return {
        "name": "instancemgmtapi",
        "version": "1.0",
        "description": "API for managing instances"
    }


def __recursiveListInstances(directory: str, instances: dict[str, dict], root: str) -> dict[str, dict]:
    # If "instance.json" is in the directory, it's an instance
    # If instance.json has "policy" as a dictionary, and has "DisallowSubdirectoryTraversal" list contains "all" or "instance", stop recursion for this directory
    if "instance.json" in os.listdir(directory):
        with open(f"{directory}/instance.json", "r") as file:
            instanceData: dict = json.load(file)
            instanceData["installedPath"] = directory.replace(root, "")
            instances[instanceData["name"]] = instanceData
            if "policy" in instanceData and "DisallowSubdirectoryTraversal" in instanceData["policy"]:
                if "all" in instanceData["policy"]["DisallowSubdirectoryTraversal"] or "instance" in instanceData["policy"]["DisallowSubdirectoryTraversal"]:
                    return instances

    # Recursively list instances in subdirectories
    for item in os.listdir(directory):
        if os.path.isdir(f"{directory}/{item}"):
            __recursiveListInstances(f"{directory}/{item}", instances, root)

    return instances


def listInstances() -> dict[str, dict]:
    # List of directories in the server root
    webroot: str = storageapi.getConfig("serverRoot")
    instances: dict[str, dict] = {}
    return __recursiveListInstances(webroot, instances, webroot)


def getInstance(name: str) -> dict:
    instances: dict[str, dict] = listInstances()
    if name in instances:
        return instances[name]
    return None
