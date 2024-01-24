BEGIN;
--
-- Create model Musician
--
CREATE TABLE `app1_musician` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `first_name` varchar(50) NOT NULL, `last_name` varchar(50) NOT NULL, `instrument` varchar(100) NOT NULL);
--
-- Create model Album
--
CREATE TABLE `app1_album` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(100) NOT NULL, `release_date` date NOT NULL, `num_stars` integer NOT NULL, `artist_id` bigint NOT NULL);
ALTER TABLE `app1_album` ADD CONSTRAINT `app1_album_artist_id_aed0987a_fk_app1_musician_id` FOREIGN KEY (`artist_id`) REFERENCES `app1_musician` (`id`);
COMMIT;
