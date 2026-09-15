DevLog API — Database Design

1. Purpose

The DevLog database stores developer accounts and their coding activity.

The initial database contains two entities:

- "users"
- "coding_sessions"

Relationship:

User 1 ───────────< CodingSession

One user can have many coding sessions, while every coding session belongs to exactly one user.

---

2. User Entity

The "users" table stores account information for developers using DevLog.

Fields

Field| Description| Constraints
"id"| Unique identifier for the user| Primary Key
"email"| Email address used for authentication| NOT NULL, UNIQUE
"password_hash"| Secure hash of the user's password| NOT NULL
"created_at"| Time when the account was created| NOT NULL
"updated_at"| Time when the account was last updated| NOT NULL

Design decisions

"id"

The user ID uniquely identifies each user.

The application should not rely on the email address as the primary identifier because email addresses can theoretically change in the future.

"email"

"email" is:

- "NOT NULL"
- "UNIQUE"

Every account must have an email address, and two accounts cannot use the same email address.

This is necessary because the initial authentication design uses email to identify the account.

"password_hash"

The database stores a password hash, not the user's original password.

Passwords must never be stored as plaintext.

Password hashing and authentication will be implemented later in M3 — Authentication.

Timestamps

"created_at" records when the user was created.

"updated_at" records when the user record was last modified.

---

3. CodingSession Entity

The "coding_sessions" table stores individual coding sessions.

Fields

Field| Description| Constraints
"id"| Unique identifier for the session| Primary Key
"user_id"| ID of the user who owns the session| Foreign Key, NOT NULL
"project_name"| Name of the project worked on| NOT NULL
"language"| Programming language used| NOT NULL
"started_at"| Time when the coding session started| NOT NULL
"ended_at"| Time when the coding session ended| NULLABLE
"description"| Optional notes about the session| NULLABLE
"created_at"| Time when the database record was created| NOT NULL
"updated_at"| Time when the database record was last updated| NOT NULL

---

4. Relationship

The relationship between the entities is:

users
  │
  │ 1
  │
  │
  │ N
  ▼
coding_sessions

A single user can own zero or many coding sessions.

A coding session must belong to exactly one user.

The relationship is implemented through:

coding_sessions.user_id → users.id

"user_id" is therefore a foreign key referencing "users.id".

---

5. User Deletion and Coding Sessions

For the initial version, deleting a user should also delete their coding sessions.

Conceptually:

DELETE User
     ↓
DELETE their CodingSessions

This can be implemented using a database foreign-key cascade.

Reason

A coding session has no meaning without its owning user in the current product design.

Therefore, leaving orphaned coding sessions after deleting a user would not be useful.

This decision can be revisited if DevLog later introduces requirements such as audit history, soft deletion, or data retention.

---

6. Duration Design

We will not store "duration" as an independent database field in the initial version.

Duration is derived from:

duration = ended_at - started_at

For example:

started_at = 10:00
ended_at   = 11:30

duration = 90 minutes

Why?

Storing both timestamps and duration creates multiple sources of truth.

For example:

started_at = 10:00
ended_at   = 11:30
duration   = 95 minutes

The database would contain contradictory information.

By deriving duration from the timestamps, the timestamps remain the source of truth.

Future consideration

If a future requirement makes storing duration necessary for performance or historical accuracy, we can revisit this decision.

We should not optimize for that requirement before it exists.

---

7. Active Coding Sessions

"ended_at" is nullable.

This allows the database to represent a coding session that has started but has not yet ended.

Example:

started_at = 2026-09-15 18:00
ended_at   = NULL

This represents an active/incomplete session.

Duration cannot be finalized until "ended_at" exists.

The application will later define how active sessions are handled by the API.

---

8. Initial Constraints

The database should enforce important rules rather than relying entirely on application code.

Initial constraints include:

Users

id           → PRIMARY KEY
email        → NOT NULL
email        → UNIQUE
password_hash → NOT NULL

Coding Sessions

id          → PRIMARY KEY
user_id     → NOT NULL
user_id     → FOREIGN KEY → users.id
project_name → NOT NULL
language    → NOT NULL
started_at  → NOT NULL

"ended_at" and "description" are initially nullable.

---

9. Initial Data Model

Conceptually:

┌─────────────────────────┐
│          users          │
├─────────────────────────┤
│ id            PK        │
│ email         UNIQUE    │
│ password_hash           │
│ created_at              │
│ updated_at              │
└────────────┬────────────┘
             │
             │ 1:N
             │
┌────────────▼────────────┐
│     coding_sessions     │
├─────────────────────────┤
│ id            PK        │
│ user_id       FK        │
│ project_name            │
│ language                │
│ started_at              │
│ ended_at                │
│ description             │
│ created_at              │
│ updated_at              │
└─────────────────────────┘

---

10. Assumptions

The initial design makes the following assumptions:

1. A user is identified by an email address.
2. Each email address can belong to only one user.
3. A coding session belongs to exactly one user.
4. A user can have many coding sessions.
5. A coding session can be active, so "ended_at" may initially be "NULL".
6. "duration" is derived rather than stored.
7. "project_name" is simple text for the initial version.
8. "language" is simple text for the initial version.
9. Projects and programming languages do not require separate tables yet.
10. Deleting a user deletes their coding sessions.
11. The initial system does not require soft deletion.
12. The database is PostgreSQL.
13. Database schema changes will be managed through migrations rather than manual production changes.

---

11. Deliberately Deferred Decisions

The following decisions are intentionally left for later milestones:

- authentication implementation
- password hashing algorithm
- JWT design
- authorization rules
- API validation
- session ownership enforcement at the API layer
- analytics queries
- indexes beyond those required by primary/unique/foreign-key constraints
- soft deletion
- project and language normalization
- storing precomputed duration
- production database deployment

These should be introduced when the corresponding requirements justify them.

---

12. Design Principle

The initial DevLog database follows a simple principle:

«Use the simplest schema that correctly represents the current requirements, and evolve it when new requirements justify the complexity.»

The database should enforce important integrity rules, while avoiding premature abstractions and unnecessary tables.