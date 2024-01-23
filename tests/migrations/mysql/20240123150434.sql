-- Create "app1_musician" table
CREATE TABLE `app1_musician` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `instrument` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) CHARSET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
-- Create "app1_album" table
CREATE TABLE `app1_album` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `release_date` date NOT NULL,
  `num_stars` int NOT NULL,
  `artist_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `app1_album_artist_id_aed0987a_fk_app1_musician_id` (`artist_id`),
  CONSTRAINT `app1_album_artist_id_aed0987a_fk_app1_musician_id` FOREIGN KEY (`artist_id`) REFERENCES `app1_musician` (`id`) ON UPDATE NO ACTION ON DELETE NO ACTION
) CHARSET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
-- Create "app2_user" table
CREATE TABLE `app2_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NULL,
  `roll` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) CHARSET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
-- Create "app2_blog" table
CREATE TABLE `app2_blog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `created_at` date NOT NULL,
  `num_stars` int NOT NULL,
  `author_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `app2_blog_author_id_1675e606_fk_app2_user_id` (`author_id`),
  CONSTRAINT `app2_blog_author_id_1675e606_fk_app2_user_id` FOREIGN KEY (`author_id`) REFERENCES `app2_user` (`id`) ON UPDATE NO ACTION ON DELETE NO ACTION
) CHARSET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
