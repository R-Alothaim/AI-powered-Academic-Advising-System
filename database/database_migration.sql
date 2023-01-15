USE `university_reviews`;

ALTER TABLE `messages`
ADD COLUMN `user_id` INT(11) NULL AFTER `chat_id`,
ADD KEY `idx_user_id` (`user_id`),
ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

UPDATE `messages` m
JOIN `chats` c ON m.chat_id = c.id
SET m.user_id = c.user_id;
