# Dynamic Flask

Very simple web server running Python for very simple tasks.

## Prepare

Requirements: Python 3.12+

```bash
pip install -r requirements.txt
```

## Start
    
```bash
python main.py
```

## Configure
You can update the DynamicFlask server by changing the configuration file `config.json`.

```json
{
    "serverRoot": "websites",
    "cacheDir": "cache",
    "storageDir": "storage",
    "host": "0.0.0.0",
    "debug": true,
    "port": 8080,
    "httpSessionSecretKey": "supersecretkey",
    "skipExtension": [".html"],
    "indexAllowed": [".py", ".html"],
    "sharedStorage": "shared"
}
```
1. `serverRoot`: This is the path where the server will look for the websites. The server will look for the website in the `serverRoot` + `request path`. For example, if the serverRoot is `websites` and the request path is `/hello`, the server will look for the website in `websites/hello`.
2. `cacheDir`: This is the path where the server will store the cache files. DynamicFlask does not do anything with the cache files, it is up to the user to decide what to do with them.
3. `storageDir`: This is the path where the server will store the files uploaded or for configuration. The storage is isolated by the instance (subdirectory of the root) and are not shared by the instances.
4. `host`: The host where the server will run.
5. `debug`: If true, the server will run in debug mode.
6. `port`: The port that the server will listen to.
7. `httpSessionSecretKey`: The secret key for the session.
8. `skipExtension`: The server will autocomplete the request even if the extension is missing. For example, if the request is `/hello` and the server finds a file `hello.html`, the server will return the content of `hello.html`. The priority is the order of the extensions in the list.
9. `indexAllowed`: Only the files with the extensions in the list will be allowed and will be bound to the directory request. For example, if the request is `/hello` where `hello` is a directory, the server will look for file like `hello/index.py` or `hello/index.html` in the directory. The priority is the order of the extensions in the list.
10. `sharedStorage`: Similar to `storageDir`, but this is the path where the subdirectory instances will share the files.

## Developing
