
db = db.getSiblingDB('backend_assignment');

db.createUser(
        {
            user: "user_api",
            pwd: "abc123xyz",
            roles: [
                {
                    role: "readWrite",
                    db: "backend_assignment"
                }
            ]
        }
);