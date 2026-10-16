# Forge Assist

Forge Assist is a command-line AI coding assistant. It sends a bounded text
snapshot of a project and a task to a chat-completions-compatible AI endpoint.
The AI proposes complete file contents as JSON. Forge Assist displays a diff
and writes the proposed files only after you type `APPLY`.

It does not execute generated code or delete files. It skips `.env` files,
common private-key files, symlinks, and common dependency/build directories
when collecting project context.

## Prerequisites

- Python 3.11 or newer
- An API key and model name for a chat-completions-compatible AI endpoint
- An internet connection to reach that endpoint

## Setup

On macOS or Linux:

```sh
chmod +x setup.sh
./setup.sh
The script creates a virtual environment, installs the package, and creates
.env from .env.example only if .env does not already exist. It is safe
to rerun; an existing .env is left unchanged*

On Windows PowerShell, run:

powershell


py -3 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e .
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Configuration
Edit .env and set:

API_BASE_URL: the provider's API base URL
API_KEY: your provider API key
MODEL: a model available to your provider
The assistant appends /chat/completions to the base URL unless that path is
already present. Alternatively, set these values as environment variables.
Environment variables take precedence over .env.

Do not commit .env or put real credentials into project files.

Usage
From the repository root, activate the environment:

sh


. .venv/bin/activate
Ask Forge Assist to make a change in the current directory:

sh


forge-assist "Create a small Flask application with a health endpoint"
Or choose a workspace explicitly:

sh


forge-assist --workspace ../my-project "Add input validation to the signup form"
You can limit the project context or set the network timeout:

sh


forge-assist --max-context-chars 50000 --timeout 120 "Add unit tests for the parser"
Inspect the displayed diff. Type APPLY exactly to write the files; press
Enter to cancel. The program does not run the generated code or tests for you.

Safety and limitations
The model receives project text, but .env files and common key files are excluded from context.
Proposed paths are checked against traversal and protected directories.
Writes are atomic per file, but a multi-file update is not a single all-or-nothing transaction.
File updates replace the complete file contents. Review every diff before applying*
The endpoint must accept a chat-completions-style request and return text at choices[0].message.content.
Generated code may be incorrect or unsafe. Review it and run your own tests*
Tests
The project uses Python's built-in unittest*

sh


python -m unittest discover -s tests -v



## Setup and use

After creating the files above:

```sh
chmod +x setup.sh
./setup.sh
Configure .env, activate the environment, then run*

sh


. .venv/bin/activate
forge-assist --workspace /path/to/your/project "Add a README and a basic test suite"
The setup script creates the virtual environment, installs the project, and copies .env.example to .env only when .env does not already exist. The tests are included, but I have not run them here. You will need to provide an AI endpoint, API key, and model name before making requests.*