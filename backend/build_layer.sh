#!/bin/bash
# Construye el layer.zip con las dependencias para Lambda
set -e

cd "$(dirname "$0")"
rm -rf layer layer.zip

mkdir -p layer/python
pip3 install -r requirements.txt -t layer/python --quiet

cd layer
zip -r ../layer.zip python/ -x "*.pyc" "__pycache__/*"
cd ..
rm -rf layer

echo "✅ layer.zip generado ($(du -h layer.zip | cut -f1))"
