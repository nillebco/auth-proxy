# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import logging
from urllib.parse import urlparse

import requests
import requests_cache
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_cache_key(request: requests.PreparedRequest, **kwargs):
    """Custom cache key function that includes the request body for POST requests."""
    key_parts = [request.method, request.url]
    if request.method == "POST":
        body_serialized = (
            base64.b64encode(request.body).decode("utf-8") if request.body else ""
        )
        key_parts.append(body_serialized)
    return hashlib.sha256(json.dumps(key_parts).encode()).hexdigest()


method_requests_mapping = {
    "GET": requests.get,
    "HEAD": requests.head,
    "POST": requests.post,
    "PUT": requests.put,
    "DELETE": requests.delete,
    "PATCH": requests.patch,
    "OPTIONS": requests.options,
}

requests_cache.install_cache(
    "cache.sqlite",
    backend="sqlite",
    allowable_methods=method_requests_mapping.keys(),
    key_fn=create_cache_key,
)


def load_yaml(file_path: str):
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}


CREDENTIALS_DICT = load_yaml("secrets/secrets.yaml")


def get_authentication_creds(path_name: str):
    parsed_url = urlparse(path_name)
    hostname = parsed_url.hostname
    creds = CREDENTIALS_DICT.get(hostname, {}) or {}
    header = creds.get("header", "x-api-key")
    value = creds.get("value", "la donna è mobile qual piùma al vento")
    logging.info(hostname, header, f"{value[:2]}..REDACTED..{value[-2:]}")
    return header, value


@app.api_route("/proxy/{path_name:path}", methods=method_requests_mapping.keys())
async def proxy(request: Request, path_name: str):
    header, value = get_authentication_creds(path_name)
    requests_function = method_requests_mapping[request.method]

    body = b""
    async for chunk in request.stream():
        body += chunk

    url = f"{path_name}?{request.query_params}"
    headers = {key: value for key, value in request.headers.items() if key != "host"}

    headers[header] = value

    outgoing_request = requests_function(url, stream=True, data=body, headers=headers)

    response = Response(
        outgoing_request.content, status_code=outgoing_request.status_code
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.api_route("/mirror/{path_name:path}", methods=method_requests_mapping.keys())
async def mirror(request: Request, path_name: str):
    content = await request.body()
    response = Response(content, status_code=200, headers=request.headers)
    return response
