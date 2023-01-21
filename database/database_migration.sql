USE `university_reviews`;

ALTER TABLE `messages`
ADD COLUMN `user_id` INT(11) NULL AFTER `chat_id`,
ADD KEY `idx_user_id` (`user_id`),
ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

UPDATE `messages` m
JOIN `chats` c ON m.chat_id = c.id
SET m.user_id = c.user_id;

ALTER TABLE `messages` MODIFY `user_id` INT(11) NOT NULL;

ALTER TABLE `chats`
ADD COLUMN `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `created_at`;

ALTER TABLE `chats`
ADD COLUMN `last_accessed` TIMESTAMP NULL DEFAULT NULL AFTER `updated_at`;

ALTER TABLE `chats`
ADD COLUMN `message_count` INT(11) NOT NULL DEFAULT 0 AFTER `title`;

ALTER TABLE `messages`
MODIFY `sender` VARCHAR(20) NOT NULL DEFAULT 'user';

ALTER TABLE `messages`
ADD CONSTRAINT `chk_sender` CHECK (`sender` IN ('user', 'bot', 'assistant', 'system'));

ALTER TABLE `chats`
ADD KEY `idx_user_updated` (`user_id`, `updated_at`);

ALTER TABLE `messages`
ADD KEY `idx_chat_timestamp` (`chat_id`, `timestamp`);

ALTER TABLE `messages`
ADD KEY `idx_user_timestamp` (`user_id`, `timestamp`);

ALTER TABLE `messages`
ADD KEY `idx_sender` (`sender`);

ALTER TABLE `chats`
ADD COLUMN `context` TEXT NULL DEFAULT NULL AFTER `title`,
ADD COLUMN `is_archived` TINYINT(1) NOT NULL DEFAULT 0 AFTER `last_accessed`,
ADD COLUMN `is_pinned` TINYINT(1) NOT NULL DEFAULT 0 AFTER `is_archived`;

ALTER TABLE `chats`
ADD KEY `idx_active_chats` (`user_id`, `is_archived`, `updated_at`);

ALTER TABLE `users`
ADD COLUMN `last_login` DATETIME NULL DEFAULT NULL AFTER `is_verified`,
ADD COLUMN `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER `created_at`;

ALTER TABLE `users`
ADD COLUMN `preferences` TEXT NULL DEFAULT NULL AFTER `last_login`;

ALTER TABLE `users`
ADD KEY `idx_verified` (`is_verified`);

UPDATE `chats` c
SET c.message_count = (
    SELECT COUNT(*) FROM `messages` m WHERE m.chat_id = c.id
);

DELIMITER $$

DROP TRIGGER IF EXISTS `messages_after_insert`$$
CREATE TRIGGER `messages_after_insert`
AFTER INSERT ON `messages`
FOR EACH ROW
BEGIN
    UPDATE `chats` 
    SET message_count = message_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.chat_id;
END$$

DROP TRIGGER IF EXISTS `messages_after_delete`$$
CREATE TRIGGER `messages_after_delete`
AFTER DELETE ON `messages`
FOR EACH ROW
BEGIN
    UPDATE `chats` 
    SET message_count = message_count - 1
    WHERE id = OLD.chat_id;
END$$

DELIMITER ;

CREATE OR REPLACE VIEW `chat_summary` AS
SELECT 
    c.id AS chat_id,
    c.user_id,
    c.title,
    c.message_count,
    c.created_at,
    c.updated_at,
    c.last_accessed,
    c.is_archived,
    c.is_pinned,
    u.name AS user_name,
    u.email AS user_email,
    (SELECT m.content FROM messages m WHERE m.chat_id = c.id ORDER BY m.timestamp DESC LIMIT 1) AS last_message,
