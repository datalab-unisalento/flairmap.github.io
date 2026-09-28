# Chatbot

This folder contains the Docker setup for the LangFlow chatbot.

## Running the Docker Compose stack

The repository provides a **Docker Compose** file (`lang-compose.yml`) that starts the LangFlow UI together with a PostgreSQL database.

1. **Create a `.env` file** (if you haven't already) in this directory. The file should define the variables referenced in `lang-compose.yml`, for example:
	```
	# Database credentials
    POSTGRES_USER=admin
    POSTGRES_PASSWORD=SET_PASSWORD
    POSTGRES_DB=langflow

    # Langflow configuration
    LANGFLOW_DATABASE_URL=postgresql://admin:lanfDBAL3@postgres:5432/langflow
    LANGFLOW_CONFIG_DIR=/app/langflow
    LANGFLOW_WORKER_TIMEOUT=800
    LANGFLOW_SUPERUSER_PASSWORD=password_sicura
    LANGFLOW_SUPERUSER_USERNAME=langflow
    LANGFLOW_AUTO_LOGIN=true
    #LANGFLOW_MCP_ENABLED=false

    #Langsmith credentials for monitoring
    LANGSMITH_TRACING=true
    LANGSMITH_ENDPOINT=https://api.smith.langchain.com
    LANGSMITH_API_KEY=<GET_API_KEY>
    LANGSMITH_PROJECT="langflow"
	# ... any other LANGFLOW_* variables you need
	```
	Adjust the values to your preferences and keep the file secure.

2. **Start the services**:
	```bash
	docker compose -f lang-compose.yml up -d
	```
	This will build the LangFlow image (if not already built) and start both `langflow` and `postgres` containers in detached mode.

3. **Access the application**:
	Open your browser at `http://localhost:7860`. The UI will be available once the containers are up and the database has initializing.

4. **Stop the stack** when you are done:
	```bash
	docker compose -f lang-compose.yml down
	```
	This shuts down the containers and removes the network, but the Docker volumes (`langflow-data` and `langflow-postgres`) persist, keeping your data across restarts.

Feel free to modify the `docker-compose.yml` (e.g., change ports or add extra environment variables) as needed for your development or production setup.
