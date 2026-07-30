# Framework Analysis Results

## Overview

This document describes the structure, components, and patterns of the test framework.


## Framework Structure

The framework has three main modules:

1. **framework/api/** - API testing components

2. **framework/ui/** - UI/Web testing components

3. **framework/core/** - Core utilities and shared components


## Base Classes


### API Components (framework/api/)

#### APIConfiguration

- **File**: `api/requests/base_api.py`

- **Import**: `from framework.api.requests.base_api import APIConfiguration`

- **Description**: Building API configuration object will be used for API calls. Contains attributes for base_url, end_point, content_type, accept_type, headers, auth, params, allow_redirects, and time_out.

- **Key Methods**:

  - `def __init__(self) -> None`
 - Initialize API configuration with default values


  - `def addHeader(self, key: str, value: str) -> None`
 - Add custom header to the configuration


  - `def addAccept(self, value: str) -> None`
 - Add Accept header to the configuration


  - `def addContentType(self, value: str) -> None`
 - Add Content-Type header to the configuration


  - `def addBasicAuth(self, username: str, password: str) -> None`
 - Add basic authentication to the configuration


#### RestRequest

- **File**: `api/requests/base_api.py`

- **Import**: `from framework.api.requests.base_api import RestRequest`

- **Description**: A wrapper around Requests to make RestFul API Calls. Contains static methods for HTTP operations like GET, POST, PUT, DELETE, PATCH.

- **Key Methods**:

  - `@staticmethod def requests_get(config: APIConfiguration) -> APIResponse`
 - Http Get request and returns APIResponse object


  - `@staticmethod def requests_post(config: APIConfiguration, data=None, json_data=None, files=None) -> APIResponse`
 - Http Post call and return API response object


  - `@staticmethod def request_put(config: APIConfiguration, data=None, json_data=None, *files) -> APIResponse`
 - Http Put request and returns API response object


  - `@staticmethod def request_delete(config: APIConfiguration, data=None) -> APIResponse`
 - Http Delete request and returns APIResponse object


  - `@staticmethod def requests_patch(config: APIConfiguration, data=None) -> APIResponse`
 - Http Patch call and returns API response object


#### APIResponse

- **File**: `api/response/response_validator.py`

- **Import**: `from framework.api.response.response_validator import APIResponse`

- **Description**: API response object. Contains status_code, text, json_response, error_msg properties for handling HTTP responses.

- **Key Methods**:

  - `def __init__(self, response: requests.Response, status_code: int, text: str, json_response: dict, error_msg: str, json_error_msg: str) -> None`
 - Initialize API response object with response data


  - `@property def status_code(self) -> int`
 - Returns HTTP status code


  - `@property def text(self) -> str`
 - Returns response text


  - `@property def json_response(self) -> dict`
 - Returns JSON response as dictionary


  - `@property def http_error_msg(self) -> str`
 - Returns HTTP error message


#### RestResponse

- **File**: `api/response/response_validator.py`

- **Import**: `from framework.api.response.response_validator import RestResponse`

- **Description**: REST Response Validator/Utility class for validation of Schema, Protocol Version, Reason Phrase, Status Code, Get Body, Get Status Code.

- **Key Methods**:

  - `@staticmethod def isSchemeHttp(response: requests.Response) -> bool`
 - Check if response scheme is HTTP


  - `@staticmethod def isSchemeHttps(response: requests.Response) -> bool`
 - Check if response scheme is HTTPS


  - `@staticmethod def isSchemeNotHttp(response: requests.Response) -> bool`
 - Check if response scheme is not HTTP


  - `@staticmethod def isSchemeNotHttps(response: requests.Response) -> bool`
 - Check if response scheme is not HTTPS


  - `@staticmethod def validate_protocol_version(response: requests.Response, expected_protocol_version: str) -> None`
 - Validates HTTP protocol version


#### JSONValidator

- **File**: `api/response/response_parser.py`

- **Import**: `from framework.api.response.response_parser import JSONValidator`

- **Description**: JSON Validator/Utility class to validate the json response body with expected json nodes/values

- **Key Methods**:

  - `@staticmethod def validate_node_in_response_body(json_data: dict, node: str, expected_value=None) -> None`
 - Validate if node exists in JSON response and optionally check its value


  - `@staticmethod def validate_node_with_jsonpath_response(json_data: dict, json_path: str, expected_value: str) -> None`
 - Validate node value using JSONPath expression


  - `@staticmethod def validate_node_list_with_jsonpath_response(json_data: dict, json_path: str, expected_list: list) -> None`
 - Validate list of nodes using JSONPath expression


  - `@staticmethod def validate_if_node_does_not_exist(json_data: dict, node: str) -> None`
 - Validate that a node does not exist in JSON response


  - `@staticmethod def get_child_nodes_from_parent_node(parent_node: dict) -> list`
 - Get all child nodes from parent node


#### CSVValidator

- **File**: `api/response/response_parser.py`

- **Import**: `from framework.api.response.response_parser import CSVValidator`

- **Description**: CSV Validator/Utility class to validate the csv response body with expected json nodes/values

- **Key Methods**:

  - `@staticmethod def validate_header_list_in_response(csv_data: list, expected_list: list) -> None`
 - Validate CSV headers match expected list


  - `@staticmethod def validate_column_list_in_response(csv_data: list, column_header: str, expected_list: list) -> None`
 - Validate column values in CSV response


  - `@staticmethod def validate_column_entry_in_response(csv_data: list, expected_column_value: str) -> None`
 - Validate specific column entry in CSV response


  - `@staticmethod def validate_row_entry_in_response(csv_data: list, expected_column_value: str) -> None`
 - Validate specific row entry in CSV response


#### XMLValidator

- **File**: `api/response/response_parser.py`

- **Import**: `from framework.api.response.response_parser import XMLValidator`

- **Description**: XML Validator/Utility class to validate the xml response body with expected json nodes/values

#### ParamsMissing

- **File**: `api/exceptions/user_defined_exceptions.py`

- **Import**: `from framework.api.exceptions.user_defined_exceptions import ParamsMissing`

- **Description**: Custom Exception class for paramaters missing

- **Key Methods**:

  - `def __init__(self, message: str) -> None`
 - Initialize exception with error message


#### InvalidURLException

- **File**: `api/exceptions/user_defined_exceptions.py`

- **Import**: `from framework.api.exceptions.user_defined_exceptions import InvalidURLException`

- **Description**: Custom Exception class for missing or invalid URL (starts with http or https)

- **Key Methods**:

  - `def __init__(self, message: str = 'Invalid URL') -> None`
 - Initialize exception with error message


#### InValidParam

- **File**: `api/exceptions/user_defined_exceptions.py`

- **Import**: `from framework.api.exceptions.user_defined_exceptions import InValidParam`

- **Description**: Custom Exception class for Invalid paramaters

- **Key Methods**:

  - `def __init__(self, message: str) -> None`
 - Initialize exception with error message



### UI Components (framework/ui/)

#### BasePage

- **File**: `ui/base/base_page.py`

- **Import**: `from framework.ui.base.base_page import BasePage`

- **Description**: This module contains base page class to provide of the base features to each sub page class.

- **Key Methods**:

  - `def __init__(self, driver) -> None`
 - Initialize base page with driver and helper objects


  - `def open_url(self, url: str) -> None`
 - Launch URL and wait for page to load


  - `def get_title(self) -> str`
 - Get page title


  - `def switch_to_nth_window(self, nth: int) -> None`
 - Switch to nth window


#### BaseActions

- **File**: `ui/base/base_actions.py`

- **Import**: `from framework.ui.base.base_actions import BaseActions`

- **Description**: This module contains all common action methods.

- **Key Methods**:

  - `def __init__(self, driver) -> None`
 - Initialize base actions with driver and helper objects


  - `def input_text(self, locator_string: str, input_text: str) -> BaseActions`
 - Input text into element


  - `def clear_value(self, locator_string: str) -> BaseActions`
 - Clear element value


  - `def get_value(self, locator_string: str) -> str`
 - Get element value attribute


  - `def get_text(self, locator_string: str) -> str`
 - Get element text


#### BaseVerifications

- **File**: `ui/base/base_verifications.py`

- **Import**: `from framework.ui.base.base_verifications import BaseVerifications`

- **Description**: This module contains all common verification methods.

- **Key Methods**:

  - `def __init__(self, driver) -> None`
 - Initialize base verifications with driver and helper objects


  - `def is_text(self, locator_string: str, expected_value: str) -> bool`
 - Verify element text matches expected value


  - `def is_value(self, locator_string: str, expected_value: str) -> bool`
 - Verify element value matches expected value


  - `def is_attribute_value(self, locator_string: str, attribute_name: str, expected_value: str) -> bool`
 - Verify element attribute value matches expected value


  - `def is_value_of_css_property(self, locator_string: str, css_property: str, expected_value: str) -> bool`
 - Verify CSS property value matches expected value


#### Locator

- **File**: `ui/base/base_locator.py`

- **Import**: `from framework.ui.base.base_locator import Locator`

- **Description**: This is module to contain commonly used functionality like find elements

- **Key Methods**:

  - `def __init__(self, driver) -> None`
 - Initialize locator with driver


  - `def get_element(self, locator: str, driver=None) -> WebElement`
 - Find element using locator string


  - `def get_elements(self, locator: str, driver=None) -> List[WebElement]`
 - Find elements using locator string


#### Wait

- **File**: `ui/base/base_wait.py`

- **Import**: `from framework.ui.base.base_wait import Wait`

- **Description**: This module contains wait selenium element using WebDriverWait

- **Key Methods**:

  - `def __init__(self, driver) -> None`
 - Initialize wait with driver


  - `def wait_for_element_until_visible(self, locator_string: str, timeout: int = 10, poll_frequency: float = 0.5, ignored_exceptions=None) -> WebElement`
 - Wait for element to be visible


  - `def wait_for_element_until_present(self, locator_string: str, timeout: int = 10, poll_frequency: float = 0.5, ignored_exceptions=None) -> WebElement`
 - Wait for element to be present


  - `def wait_for_element_until_clickable(self, locator_string: str, timeout: int = 10, poll_frequency: float = 0.5, ignored_exceptions=None) -> WebElement`
 - Wait for element to be clickable


  - `def wait_for_element_until_not_visible(self, locator_string: str, timeout: int = 10, poll_frequency: float = 0.5, ignored_exceptions=None) -> bool`
 - Wait for element to not be visible


#### Browser

- **File**: `ui/utils/browser.py`

- **Import**: `from framework.ui.utils.browser import Browser`

- **Description**: Browser utility class for creating and managing WebDriver instances with support for local and remote execution.

- **Key Methods**:

  - `@classmethod def get_driver(cls, settings: dict = {'browser': 'chrome', 'environment': 'local', 'headless': 'false'}) -> WebDriver`
 - Get WebDriver instance based on settings


  - `@classmethod def get_local_driver_instance(cls, settings: dict) -> WebDriver`
 - Get local WebDriver instance


  - `@classmethod def get_remote_driver_instance(cls, settings: dict) -> WebDriver`
 - Get remote WebDriver instance for grid execution


  - `@staticmethod def set_chrome_driver_options(settings: dict) -> Options`
 - Set Chrome driver options based on settings


#### BrowserException

- **File**: `ui/exceptions/user_defined_exceptions.py`

- **Import**: `from framework.ui.exceptions.user_defined_exceptions import BrowserException`

- **Description**: Custom exception class for all browsers.

- **Key Methods**:

  - `def __init__(self, message: str = 'Invalid browser passed') -> None`
 - Initialize browser exception with error message


#### ElementNotFound

- **File**: `ui/exceptions/user_defined_exceptions.py`

- **Import**: `from framework.ui.exceptions.user_defined_exceptions import ElementNotFound`

- **Description**: Custom exception class for all Elements.

- **Key Methods**:

  - `def __init__(self, message: str = 'Element not found') -> None`
 - Initialize element not found exception with error message



### Core Components (framework/core/)

#### LoggerFactory

- **File**: `core/utils/logger_factory.py`

- **Import**: `from framework.core.utils.logger_factory import LoggerFactory`

- **Description**: This module logger Factory class to configure and get logger as per ini file.

- **Key Methods**:

  - `@classmethod def get_conf_file_path(cls) -> str`
 - Get configuration file path for logger


  - `@classmethod def get_logger(cls, logger_name: str = 'COLLAB') -> logging.Logger`
 - Get configured logger instance


#### PropFileReader

- **File**: `core/utils/prop_file_reader.py`

- **Import**: `from framework.core.utils.prop_file_reader import PropFileReader`

- **Description**: This module to read different (Common and Environment) properties files and to provide in single object.

- **Key Methods**:

  - `@classmethod def load_config_prop(cls) -> None`
 - Load configuration properties from file


  - `@classmethod def load_env_prop(cls) -> None`
 - Load environment properties from file


  - `@classmethod def load_all_props(cls) -> None`
 - Load all properties (config and environment)


#### ConfConst

- **File**: `core/constants/core_constants.py`

- **Import**: `from framework.core.constants.core_constants import ConfConst`

- **Description**: Module to contain all constants of framework - configuration file paths

#### LogConst

- **File**: `core/constants/core_constants.py`

- **Import**: `from framework.core.constants.core_constants import LogConst`

- **Description**: Module to contain all constants of framework - logging constants


## Client Class

- **Name**: RestRequest

- **Module**: API

- **File**: `api/requests/base_api.py`

- **Import**: `from framework.api.requests.base_api import RestRequest`

- **Description**: A wrapper around Requests to make RestFul API Calls. Contains static methods for HTTP operations like GET, POST, PUT, DELETE, PATCH.

- **Key Methods**:

  - `@staticmethod def requests_get(config: APIConfiguration) -> APIResponse`
 - Http Get request and returns APIResponse object


  - `@staticmethod def requests_post(config: APIConfiguration, data=None, json_data=None, files=None) -> APIResponse`
 - Http Post call and return API response object


  - `@staticmethod def request_put(config: APIConfiguration, data=None, json_data=None, *files) -> APIResponse`
 - Http Put request and returns API response object


  - `@staticmethod def request_delete(config: APIConfiguration, data=None) -> APIResponse`
 - Http Delete request and returns APIResponse object


  - `@staticmethod def requests_patch(config: APIConfiguration, data=None) -> APIResponse`
 - Http Patch call and returns API response object



## Response Class

- **Name**: APIResponse

- **Module**: API

- **File**: `api/response/response_validator.py`

- **Import**: `from framework.api.response.response_validator import APIResponse`

- **Description**: API response object. Contains status_code, text, json_response, error_msg properties for handling HTTP responses.

- **Key Methods**:

  - `@property def status_code(self) -> int`
 - Returns HTTP status code


  - `@property def text(self) -> str`
 - Returns response text


  - `@property def json_response(self) -> dict`
 - Returns JSON response as dictionary


  - `@property def http_error_msg(self) -> str`
 - Returns HTTP error message


  - `@property def response(self) -> requests.Response`
 - Returns raw response object



## Assertion Utilities

- **Name**: RestResponse

- **Module**: API

- **File**: `api/response/response_validator.py`

- **Import**: `from framework.api.response.response_validator import RestResponse`

- **Signature**: `class RestResponse with static methods for response validation`

- **Description**: REST Response Validator/Utility class for validation of Schema, Protocol Version, Reason Phrase, Status Code, Get Body, Get Status Code.

- **Usage Pattern**: RestResponse.validate_status_code(response.response, 200); RestResponse.validate_protocol_version(response.response, '1.1')


## Utility Functions


### API Utilities (framework/api/)

#### build_url

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import build_url`

- **Signature**: `def build_url(config: APIConfiguration) -> str`

- **Description**: Builds url from APIConfiguration object and returns url

- **Usage Pattern**: url = build_url(config)

#### handle_http_error

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import handle_http_error`

- **Signature**: `def handle_http_error(response: requests.Response) -> str`

- **Description**: Builds and returns HTTP Error Message for 400 and 500 Status codes

- **Usage Pattern**: error_msg = handle_http_error(response)

#### check_json_response

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import check_json_response`

- **Signature**: `def check_json_response(response: requests.Response) -> tuple`

- **Description**: Converts given json response to pretty json reposnse

- **Usage Pattern**: error_msg, response_json = check_json_response(response)

#### rest_response_handle

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import rest_response_handle`

- **Signature**: `def rest_response_handle(response: requests.Response) -> tuple`

- **Description**: This Method handles http repsonse by checking the status code and building error message if needed or response if status is OK

- **Usage Pattern**: response, status_code, text, json_response, http_err_msg, json_err_msg = rest_response_handle(response)

#### convert_to_json

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import convert_to_json`

- **Signature**: `def convert_to_json(data: dict) -> str`

- **Description**: Converts given data to json format

- **Usage Pattern**: json_string = convert_to_json(data)

#### files_to_upload

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import files_to_upload`

- **Signature**: `def files_to_upload(path: list) -> list`

- **Description**: builds a list of tuples each with file name and file descripter

- **Usage Pattern**: files = files_to_upload(file_paths)

#### validate_params

- **File**: `api/helpers/helper_api.py`

- **Import**: `from framework.api.helpers.helper_api import validate_params`

- **Signature**: `def validate_params(*args) -> bool`

- **Description**: Checks args count, True only if any one of the args is not None. In all other cases it returns False

- **Usage Pattern**: valid = validate_params(data, json_data, files)

#### deserialize

- **File**: `api/response/response_parser.py`

- **Import**: `from framework.api.response.response_parser import deserialize`

- **Signature**: `def deserialize(response: requests.Response, content_type: str) -> dict`

- **Description**: Response Parser Factory for returning either JSON, XML, or CSV data

- **Usage Pattern**: parsed_data = deserialize(response, 'application/json')


### UI Utilities (framework/ui/)

#### get_locator_by

- **File**: `ui/common/helper.py`

- **Import**: `from framework.ui.common.helper import get_locator_by`

- **Signature**: `def get_locator_by(locator: str) -> tuple`

- **Description**: This module contains all the helper functions, which can be directly used. Converts locator string to By locator tuple.

- **Usage Pattern**: by_locator = get_locator_by('id|element_id')


### Core Utilities (framework/core/)

#### register

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import register`

- **Signature**: `def register(func) -> func`

- **Description**: Register a function as a plug-in

- **Usage Pattern**: @register decorator to register functions as plugins

#### slow_down

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import slow_down`

- **Signature**: `def slow_down(func) -> func`

- **Description**: Sleep 1 second before calling the function

- **Usage Pattern**: @slow_down decorator to add delay before function execution

#### debug

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import debug`

- **Signature**: `def debug(func) -> func`

- **Description**: Print the function signature and return value

- **Usage Pattern**: @debug decorator to log function calls and returns

#### timer

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import timer`

- **Signature**: `def timer(func) -> func`

- **Description**: Print the runtime of the decorated function

- **Usage Pattern**: @timer decorator to measure function execution time

#### handle_on_exceptions

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import handle_on_exceptions`

- **Signature**: `def handle_on_exceptions(exceptions=(), msg_on_exception='', replacement=None) -> func`

- **Description**: A decorator that wraps the passed in function and logs exceptions should one occur

- **Usage Pattern**: @handle_on_exceptions(exceptions=TimeoutException, msg_on_exception='Element not found')

#### avoid_exceptions

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import avoid_exceptions`

- **Signature**: `def avoid_exceptions(exceptions=(), replacement=None, msg_on_exception=None) -> func`

- **Description**: A decorator that wraps the passed in function and logs exceptions should one occur

- **Usage Pattern**: @avoid_exceptions(exceptions=NoSuchElementException, replacement=False)

#### retry_on_exception

- **File**: `core/common/decorators.py`

- **Import**: `from framework.core.common.decorators import retry_on_exception`

- **Signature**: `def retry_on_exception(tries: int = 3, delay: int = 3, backoff: int = 2, max_delay: int = 15) -> func`

- **Description**: Decorator for implementing exponential backoff for retrying on failures.

- **Usage Pattern**: @retry_on_exception(tries=3, delay=3, backoff=2, max_delay=15)


## Test Patterns

### Test Setup

- Configuration setup: config = APIConfiguration(); config.base_url = 'https://api.example.com'; config.end_point = '/api/v1/users'

- Header setup: config.addHeader('Authorization', 'Bearer token'); config.addContentType('application/json')

- UI setup: driver = Browser.get_driver({'browser': 'chrome', 'environment': 'local'}); page = BasePage(driver)

### Assertions

- RestResponse.validate_status_code(response.response, 200)

- RestResponse.validate_protocol_version(response.response, '1.1')

- RestResponse.validate_reason_phrase(response.response, 'OK')

- JSONValidator.validate_node_in_response_body(json_data, 'key', 'expected_value')

- assert response.json_response['key'] == 'value'

- assert page.verify.is_text('id|element', 'expected_text')

- assert page.verify.is_displayed('xpath|//button')

### Request Patterns

- GET: response = RestRequest.requests_get(config)

- POST: response = RestRequest.requests_post(config, json_data=data)

- PUT: response = RestRequest.request_put(config, data=data)

- DELETE: response = RestRequest.request_delete(config)

- PATCH: response = RestRequest.requests_patch(config, data=data)

### Response Handling

- Status code: status = response.status_code

- JSON data: json_data = response.json_response

- Response text: text = response.text

- Raw response: raw = response.response

- Error handling: if response.http_error_msg: handle_error()

### Status Checks

- RestResponse.validate_status_code(response.response, 200)

- assert response.status_code == 200

- if response.status_code in [200, 201, 202]: success_handler()

### Content Checks

- JSONValidator.validate_node_in_response_body(response.json_response, 'data')

- assert 'key' in response.json_response

- JSONValidator.validate_node_with_jsonpath_response(response.json_response, '$.data.id', expected_id)

### Error Checks

- if response.http_error_msg: logger.error(response.http_error_msg)

- if response.json_error_msg: handle_json_error()

- try: json_data = response.json_response except: handle_invalid_json()


## Test Organization

### Test Markers

- @pytest.mark.api

- @pytest.mark.ui

- @pytest.mark.smoke

- @pytest.mark.regression

### Grouping Strategy

Tests organized by type (api/, ui/) and feature modules

### Common Test Method Signatures

- `def test_api_get_request(self):`

- `def test_ui_login_functionality(self):`

### Data Setup Patterns

- APIConfiguration setup for API tests

- Browser and page object setup for UI tests

- Property file loading for environment configuration


## Framework Conventions

### Naming

CamelCase for classes (APIConfiguration, RestRequest), snake_case for methods (requests_get, validate_status_code)

### Organization

Modular structure: api/ for API components, ui/ for UI components, core/ for common utilities

### Structure

Base classes in base/ directories, utilities in utils/ and helpers/, exceptions in exceptions/

### Documentation

Comprehensive docstrings in classes and methods explaining purpose and usage

### Error Handling

Custom exception classes for different error types, decorator-based exception handling

### Validation

Static validation methods in RestResponse, JSONValidator, CSVValidator classes


## Validation Patterns

### Status Checks

- RestResponse.validate_status_code(response.response, 200)

- assert response.status_code == 200

- Check status code in range: if 200 <= response.status_code < 300

### Content Checks

- JSONValidator.validate_node_in_response_body(json_data, 'key', 'expected_value')

- JSONValidator.validate_node_with_jsonpath_response(json_data, '$.data.id', expected_id)

- assert response.json_response['key'] == 'value'

- Verify response contains key: assert 'data' in response.json_response

### Error Checks

- Check HTTP error message: if response.http_error_msg: handle_error()

- Check JSON error: if response.json_error_msg: handle_json_error()

- Validate error response structure: JSONValidator.validate_node_in_response_body(error_response, 'error')

### Custom Checks

- Protocol validation: RestResponse.validate_protocol_version(response.response, '1.1')

- Scheme validation: RestResponse.isSchemeHttps(response.response)

- Reason phrase validation: RestResponse.validate_reason_phrase(response.response, 'OK')

- UI element validation: page.verify.is_displayed('id|element')

- UI text validation: page.verify.is_text('xpath|//h1', 'Expected Title')
