#!/bin/bash

# Wait for MongoDB instances to start
until mongo --host mongo1 --eval "printjson(rs.status())" | grep "ok"; do
    echo "Waiting for MongoDB to initialize..."
    sleep 5
done

# Initialize replica set
mongo --host mongo1 --eval "rs.initiate({_id: 'rs0', members: [{_id: 0, host: 'mongo1:27017'}, {_id: 1, host: 'mongo2:27017'}, {_id: 2, host: 'mongo3:27017'}]})"

# Wait for a longer time to allow replica set configuration to take effect
sleep 30

# Create admin user
mongo --host mongo1 admin --eval "db.createUser({ user: 'admin', pwd: 'admin123', roles: [ { role: 'root', db: 'admin' } ] })"

# Wait for user creation to propagate
sleep 5

# Check replica set status
mongo --host mongo1 admin --eval "rs.status()"