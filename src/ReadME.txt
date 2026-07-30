# API Project Setup and Execution Guide

## Requirements
    - Python 3.13
    - Poetry for dependency management
    - Git for version control


## 1. Clone the Repository
    To get started, clone the repository to your local machine:

    ```bash
    git clone <repository-url>
    cd src
    ```

## 2. Poetry Setup
    This project uses Poetry for dependency management. Follow these steps to set up the project:

    ### Install Poetry (if not already installed):
    On Windows:
    ```bash
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    ```
    On macOS/Linux:
    ```bash
    curl -sSL https://install.python-poetry.org | python -
    ```

## 3. Activate Virtual Environment
    You can activate the Poetry virtual environment using either method:

    ### Method 1: Using poetry shell (recommended)
    ```bash
    poetry shell
    ```
    This opens a new shell with the virtual environment activated.

    ### Method 2: Using poetry env activate
    On Windows (PowerShell):
    ```bash
    & (poetry env info --path)\Scripts\Activate.ps1
    ```
    On Windows (Command Prompt):
    ```bash
    poetry env info --path
    # Copy the path and run: <path>\Scripts\activate.bat
    ```
    On macOS/Linux:
    ```bash
    source $(poetry env info --path)/bin/activate
    ```

    Note: `poetry env activate` is not a direct Poetry command. Use the above commands to manually activate the environment created by Poetry.

## 4. Install Project Dependencies
    After activating the virtual environment, install the project dependencies:
    ```bash
    poetry install
    ```

## 5. Configure Environment Variables
    In .env file, set the required environment variables such as OpenAI API key, log directory, and test framework path.

## 6. Run the Application
    You can run the application using the following command:
    ```bash
    python run_app.py
    ```