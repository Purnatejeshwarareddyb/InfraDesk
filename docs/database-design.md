# Database design

SQLite by default (single computer, no extra service). The schema is created by Alembic migration
`0001_initial_schema`; the container runs `alembic upgrade head` at start. SQLite is right for a
local prototype; many simultaneous users in production would call for PostgreSQL (the code uses
SQLAlchemy and no SQLite-only SQL, but this has not been tested on PostgreSQL).

```mermaid
erDiagram
    users ||--o{ tickets : "reports (reporter_id)"
    users ||--o{ tickets : "works on (assignee_id)"
    assets ||--o{ tickets : "related_asset_id"
    tickets ||--o{ ticket_comments : has
    users ||--o{ ticket_comments : writes
    tickets ||--o{ audit_events : "history (ticket_id, optional)"
    users ||--o{ audit_events : "actor_id"
    users ||--o{ notifications : "recipient_user_id"
    tickets ||--o{ notifications : "ticket_id, optional"

    users {
        int id PK
        string username UK
        string display_name
        string password_hash
        string role "ADMIN or WORKER"
        bool is_active
        datetime created_at
        datetime updated_at
    }
    tickets {
        int id PK
        string ticket_number UK "HD-000001"
        string title
        text description
        string category
        string priority
        string status
        int reporter_id FK
        int assignee_id FK "nullable"
        int related_asset_id FK "nullable"
        text resolution_note
        datetime created_at
        datetime updated_at
        datetime resolved_at
        datetime closed_at
    }
    ticket_comments {
        int id PK
        int ticket_id FK
        int author_id FK
        text body
        datetime created_at
    }
    audit_events {
        int id PK
        int ticket_id FK "null for admin events"
        int actor_id FK
        string event_type
        string old_value
        string new_value
        text detail
        datetime created_at
    }
    notifications {
        int id PK
        int recipient_user_id FK
        int ticket_id FK "nullable"
        string type
        string message
        datetime read_at "null = unread"
        datetime created_at
    }
    assets {
        int id PK
        string asset_tag UK
        string name
        string asset_type
        string location
        string serial_number "nullable"
        string status "ACTIVE, IN_REPAIR, RETIRED"
        text notes
        datetime created_at
        datetime updated_at
    }
```

## Decisions

- **History table:** the specification allowed `ticket_history` or a generic audit table. InfraDesk uses one
  generic `audit_events` table. Rows with a `ticket_id` are the per-ticket history; rows without one record user and
  asset administration (the Activity page).
- **No hard deletes of referenced records.** All foreign keys use `ON DELETE RESTRICT`; users are deactivated and assets
  are retired, tickets are cancelled or closed. History can never disappear by cascade.
- **UTC everywhere.** A custom column type stores naive UTC and always returns timezone-aware UTC; the browser shows local time.
- **Indexes** on the filtered columns: ticket status, category, reporter, assignee, created date, status+priority; username,
  ticket number, asset tag; notification recipient + read state; audit ticket and date.
- **Enums are stored as short strings** (not native database enums), so adding a value needs no table rebuild.
- **Passwords** are stored only as Argon2 hashes and never returned by any endpoint.
