import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import azure.functions as func
import logging
import json
from fastapi import FastAPI

from app.api.router import api_router

app_fastapi = FastAPI()
app_fastapi.include_router(api_router)

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="{*route}")
async def func_asher_chatbot(req: func.HttpRequest) -> func.HttpResponse:
    """
    The main entry point for the Azure Function.
    This function will proxy requests to the FastAPI app using ASGI.
    """
    # Get the request path and method
    route = req.route_params.get('route', '')
    if route:
        path = '/' + route
    else:
        path = '/'
    
    method = req.method
    logging.info(f"Received {method} request to {path}")
    
    # Log all available query parameters for debugging
    logging.info(f"Query parameters: {dict(req.params)}")
    
    # Log all available headers for debugging
    logging.info(f"Headers: {dict(req.headers)}")
    
    # Get query parameters
    params = {}
    for param_name, param_value in req.params.items():
        if param_name != 'code':  # Exclude Azure Functions authorization code
            params[param_name] = param_value
    
    query_string = b'&'.join([f"{k}={v}".encode() for k, v in params.items()])
    logging.info(f"Query string: {query_string}")
    
    # Get headers (excluding Azure Functions headers)
    headers = []
    for key, value in req.headers.items():
        if key.lower() not in ('host', 'x-forwarded-for', 'x-functions-key'):
            headers.append((key.lower().encode(), value.encode()))
    
    body = req.get_body()
    if body:
        logging.info(f"Request body: {body.decode('utf-8', errors='replace')}")
    
    # Add content-type header if not present and body exists
    if body and not any(k == b'content-type' for k, _ in headers):
        headers.append((b'content-type', b'application/json'))
    
    # Create ASGI scope
    scope = {
        'type': 'http',
        'asgi': {'version': '3.0', 'spec_version': '2.1'},
        'http_version': '1.1',
        'method': method,
        'scheme': 'https',
        'path': path,
        'raw_path': path.encode(),
        'query_string': query_string,
        'headers': headers,
        'server': ('azure-functions', ''),
        'client': ('', 0),
    }
    
    # Create ASGI receive channel
    async def receive():
        return {
            'type': 'http.request',
            'body': body or b'',
            'more_body': False,
        }
    
    # Create ASGI send channel
    response_status = None
    response_headers = []
    response_body = bytearray()
    
    async def send(message):
        nonlocal response_status, response_headers, response_body
        
        if message['type'] == 'http.response.start':
            response_status = message['status']
            response_headers = message.get('headers', [])
        
        elif message['type'] == 'http.response.body':
            response_body.extend(message.get('body', b''))
    
    try:
        # Run the ASGI application
        await app_fastapi(scope, receive, send)
        
        # Convert headers to dict for Azure Functions
        headers_dict = {}
        for key, value in response_headers:
            key_str = key.decode('utf-8')
            value_str = value.decode('utf-8')
            headers_dict[key_str] = value_str
        
        logging.info(f"Response status: {response_status}")
        if response_body:
            try:
                body_snippet = response_body[:200].decode('utf-8', errors='replace')
                logging.info(f"Response body (partial): {body_snippet}...")
            except Exception:
                logging.info("Could not log response body due to encoding issues")
        
        # Return the Azure Functions HTTP response
        return func.HttpResponse(
            body=bytes(response_body),
            status_code=response_status,
            headers=headers_dict
        )
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )