# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202505311458_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS staff (
        id UUID,
        first_name VARCHAR(16) NOT NULL,
        last_name VARCHAR(16) NOT NULL,
        position VARCHAR(64) NOT NULL,
        education JSON NOT NULL,
        experience JSON NOT NULL,
        activity JSON NOT NULL,
        other_details JSON,
        public BOOL DEFAULT TRUE,
        active BOOL DEFAULT TRUE,
        CONSTRAINT pk_staff PRIMARY KEY (id),
        CONSTRAINT fk_staff_users FOREIGN KEY (id) REFERENCES users(id)
    );
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS staff;
    """
]
