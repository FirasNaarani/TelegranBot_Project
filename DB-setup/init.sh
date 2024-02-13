# change owner & permission of a key file 
#!/bin/bash
sleep 10
chmod 400 /key
chown 999:999 /key
mongod --replSet rs0 --bind_ip_all --keyFile /key --fork --logpath /var/log/mongodb/mongod.log
wait

if mongosh ./initiate.js; then
    echo "SUCCESS >> initiate"
else
    echo "FAILURE >> initiate"
    exit 1
fi
sleep 30

if mongosh ./createUser.js; then
    echo "SUCCESS >> createUser"
else
    echo "FAILURE >> createUser"
    exit 1
fi
sleep 5

if mongosh --host mongo1:27017 -u admin -p admin ./reconfig.js; then
    echo "SUCCESS >> reConfig"
else
    echo "FAILURE >> reConfig"
    exit 1
fi
sleep 5