-- ==========================================================================
-- Student Buddy AI — MySQL Schema
-- ==========================================================================
-- Run this script to set up the database manually.
-- The application also creates tables automatically on first run if they
-- don't exist, so running this script is optional.
--
-- Usage:
--   mysql -u root -p < database/schema.sql
-- ==========================================================================

-- Create the database (skip if you already created it)
CREATE DATABASE IF NOT EXISTS student_buddy_ai
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE student_buddy_ai;

-- Create a dedicated application user (adjust password as needed)
-- You can skip this if you prefer to use an existing MySQL user.
-- CREATE USER IF NOT EXISTS 'student_buddy'@'localhost'
--     IDENTIFIED BY 'CHOOSE_A_STRONG_PASSWORD';
-- GRANT SELECT, INSERT, UPDATE, DELETE, CREATE
--     ON student_buddy_ai.* TO 'student_buddy'@'localhost';
-- FLUSH PRIVILEGES;

-- Interaction history table
CREATE TABLE IF NOT EXISTS interaction_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    session_id  VARCHAR(64)     NOT NULL        COMMENT 'Anonymous session identifier',
    action      VARCHAR(50)     NOT NULL        COMMENT 'hint, approach, explain, debug, practice',
    language    VARCHAR(20)     NOT NULL DEFAULT 'Python' COMMENT 'Programming language',
    question    TEXT            NOT NULL        COMMENT 'User question or code snippet',
    response    MEDIUMTEXT      NOT NULL        COMMENT 'Assistant response',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_session (session_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
