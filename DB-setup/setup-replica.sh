#!/bin/bash

# Wait for MongoDB instances to start
until mongo --host mongo1 --eval "printjson(rs.status())" | grep "ok"; do
    echo "Waiting for MongoDB to initialize..."
    sleep 5
done

# Initialize replica set
mongo --host mongo1 --eval "var initFunc = function() { $(cat init-replica.js); }; initFunc()"

# Wait for a longer time to allow replica set configuration to take effect
sleep 30

# Create admin user
mongo --host mongo1 admin init-db.js

# Wait for user creation to propagate
sleep 5

# Check replica set status
mongo --host mongo1 admin --eval "rs.status()"