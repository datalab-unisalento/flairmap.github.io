# FLAIR MCP SERVER

## Project Structure

## Requirements
- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) (recommended for dependency management)

## Setup
To set up the project locally using `uv`, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FLAIR-MCP
   ```

2. **Create the virtual environment and install dependencies**:
   ```bash
   uv sync
   ```

3. **Configure environment variables**:
   Create a `.env` file in the project root based on the server's needs (optional, default values are provided).

## Execution

### Local Execution with `uv`
To start the MCP server via `stdio`:
```bash
uv run flair-mcp
```

## Building the Application

To build the application for distribution (creating wheel and sdist):

```bash
uv build
```

The build artifacts will be located in the `dist/` directory.

## MCP Client Configuration

To use this server with an MCP client (such as Claude Desktop), add the configuration to your client's configuration file (e.g., `claude_desktop_config.json`).

### Claude Desktop Configuration Example

Replace `/path/to/FLAIR-MCP` with the absolute path to your project folder.

#### Using `uv` (Recommended)
```json
{
  "mcpServers": {
    "flair-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/FLAIR-MCP",
        "run",
        "flair-mcp"
      ]
    }
  }
}
```