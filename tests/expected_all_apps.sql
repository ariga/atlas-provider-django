-- atlas:pos app1_musician[type=table] [ABS_PATH]/tests/app1/models.py:4:1-7:50
-- atlas:pos app1_album[type=table] [ABS_PATH]/tests/app1/models.py:10:1-14:38
-- atlas:pos app2_user[type=table] [ABS_PATH]/tests/app2/models.py:4:1-7:44
-- atlas:pos app2_blog[type=table] [ABS_PATH]/tests/app2/models.py:10:1-14:38

--
-- Create model Musician
--
CREATE TABLE `app1_musician` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(50) NOT NULL, `last_name` varchar(50) NOT NULL, `instrument` varchar(100) NOT NULL);
--
-- Create model Album
--
CREATE TABLE `app1_album` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `release_date` date NOT NULL, `num_stars` integer NOT NULL, `artist_id` bigint NOT NULL);
ALTER TABLE `app1_album` ADD CONSTRAINT `app1_album_artist_id_aed0987a_fk_app1_musician_id` FOREIGN KEY (`artist_id`) REFERENCES `app1_musician` (`id`);
--
-- Create model User
--
CREATE TABLE `app2_user` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(50) NOT NULL, `last_name` varchar(50) NULL, `roll` varchar(100) NOT NULL);
--
-- Create model Blog
--
CREATE TABLE `app2_blog` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `created_at` date NOT NULL, `num_stars` integer NOT NULL, `author_id` bigint NOT NULL);
ALTER TABLE `app2_blog` ADD CONSTRAINT `app2_blog_author_id_1675e606_fk_app2_user_id` FOREIGN KEY (`author_id`) REFERENCES `app2_user` (`id`);
