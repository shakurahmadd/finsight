#!/bin/bash
until pg_isready -h db -p 5432; do
    echo "Waiting for database..."
    sleep 1
done
alembic upgrade head
uvicorn api.main:app --host 0.0.0.0