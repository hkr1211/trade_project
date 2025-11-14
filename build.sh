#!/bin/bash

# 收集静态文件
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Static files collected successfully!"
