#!/usr/bin/env bash
set -e


# Create an admin user
superset fab create-admin \
              --username admin \
              --firstname Superset \
              --lastname Admin \
              --email admin@superset.com \
              --password admin

superset db upgrade
superset superset init

