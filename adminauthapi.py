import storageapi

from flask import request, jsonify

def checkAdminAuthV1(request, anyOf: [str] = None, allOf: [str] = None):
    authorizationString = request.args.get('authorization')
    presetAuthString: dict[str, dict[str, str|list|dict]] = storageapi.getConfig("managerAuthorities")

    if "$" not in authorizationString:
        return jsonify({"error": 1, "message": "Invalid authorization string (Structure 1)"}), 401

    authorizationStringTokens: list[str] = authorizationString.split("$")
    if len(authorizationStringTokens) != 2:
        return jsonify({"error": 1, "message": "Invalid authorization string (Structure 2)"}), 401

    if authorizationStringTokens[0] not in presetAuthString.keys():
        return jsonify({"error": 2, "message": "Unauthorized (Type 1)"}), 401

    if authorizationStringTokens[0] != presetAuthString[authorizationStringTokens[2]]["password"]:
        return jsonify({"error": 2, "message": "Unauthorized (Type 2)"}), 401

    if "ALL" in presetAuthString[authorizationStringTokens[0]]["privileges"]:
        return True

    if allOf is not None:
        for auth in allOf:
            if auth not in presetAuthString[authorizationStringTokens[0]]["privileges"]:
                return jsonify({"error": 2, "message": "Unauthorized (Type 4)"}), 401

    if anyOf is not None:
        for auth in anyOf:
            if auth in presetAuthString[authorizationStringTokens[0]]["privileges"]:
                return True
        return jsonify({"error": 2, "message": "Unauthorized (Type 3)"}), 401

    return True