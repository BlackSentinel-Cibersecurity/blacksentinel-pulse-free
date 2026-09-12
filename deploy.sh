#!/bin/bash
set -e

echo "=========================================="
echo "  BlackSentinel Pulse - One-Command Deploy"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Install Docker Desktop: https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "Docker daemon is not running."

    # Try to start Docker Desktop on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Attempting to start Docker Desktop..."
        if [ -d "/Applications/Docker.app" ]; then
            open -a Docker
            echo "Waiting for Docker daemon to start..."
            for i in $(seq 1 60); do
                if docker info &> /dev/null; then
                    echo "Docker daemon is ready!"
                    break
                fi
                if [ $i -eq 60 ]; then
                    echo "ERROR: Docker daemon did not start within 60 seconds."
                    echo "Please start Docker Desktop manually and try again."
                    exit 1
                fi
                sleep 1
                echo -n "."
            done
            echo ""
        else
            echo "ERROR: Docker Desktop not found in /Applications."
            echo "Install Docker Desktop: https://docs.docker.com/desktop/install/mac-install/"
            exit 1
        fi
    else
        echo "Please start Docker daemon manually and try again."
        exit 1
    fi
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env

    # Generate SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)

    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your_strong_db_password_here/$DB_PASSWORD/" .env
        sed -i '' "s|generate_with:.*|$SECRET_KEY|" .env
    else
        sed -i "s/your_strong_db_password_here/$DB_PASSWORD/" .env
        sed -i "s|generate_with:.*|$SECRET_KEY|" .env
    fi

    echo ".env created with auto-generated secrets"
fi

echo ""
echo "Building and starting services..."
echo ""

# Use docker compose (v2) or docker-compose (v1)
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

echo ""
echo "=========================================="
echo "  BlackSentinel Pulse Deployed!"
echo "=========================================="
echo ""
echo "  Frontend: http://localhost"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/api/docs"
echo ""
echo "  Default credentials:"
echo "    Username: admin"
echo "    Password: admin123"
echo ""
echo "  IMPORTANT: Change the default password!"
echo ""
