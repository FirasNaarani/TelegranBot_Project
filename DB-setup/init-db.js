// create-admin-user.js
db.createUser({
    user: 'admin',
    pwd: 'admin123',
    roles: [
        { role: 'root', db: 'admin' }
    ]
});