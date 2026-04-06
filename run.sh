#!/bin/bash
echo "🚀 Starting Gunicorn server..."
gunicorn config.wsgi:application