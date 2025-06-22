# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202506121032_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS parents (
        id UUID,
        fathers_name VARCHAR(64) NOT NULL,
        mothers_name VARCHAR(64) NOT NULL,
        fathers_email_id VARCHAR(64) NOT NULL,
        mothers_email_id VARCHAR(64) NOT NULL,
        fathers_contact_no VARCHAR(15) NOT NULL,
        mothers_contact_no VARCHAR(15) NOT NULL,
        address TEXT NOT NULL,
        extra_info JSON,
        is_active BOOLEAN DEFAULT TRUE,
        CONSTRAINT pk_parents PRIMARY KEY (id),
        CONSTRAINT fk_parents_users FOREIGN KEY (id,is_active) REFERENCES users(id,is_active) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX uniq_fathers_email_id ON parents(fathers_email_id,is_active) WHERE is_active;
    """,
    """--sql
    CREATE UNIQUE INDEX uniq_mothers_email_id ON parents(mothers_email_id,is_active) WHERE is_active;
    """,
    """--sql
    CREATE UNIQUE INDEX uniq_fathers_contact_no ON parents(fathers_contact_no,is_active) WHERE is_active;
    """,
    """--sql
    CREATE UNIQUE INDEX uniq_mothers_contact_no ON parents(mothers_contact_no,is_active) WHERE is_active;
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_fathers_email_id;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_mothers_email_id;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_fathers_contact_no;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_mothers_contact_no;
    """,
    """--sql
    DROP TABLE IF EXISTS parents;
    """,
]
