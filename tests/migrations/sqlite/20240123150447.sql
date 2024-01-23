-- Create "app1_musician" table
CREATE TABLE `app1_musician` (
  `id` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `first_name` varchar NOT NULL,
  `last_name` varchar NOT NULL,
  `instrument` varchar NOT NULL
);
-- Create "app1_album" table
CREATE TABLE `app1_album` (
  `id` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar NOT NULL,
  `release_date` date NOT NULL,
  `num_stars` integer NOT NULL,
  `artist_id` bigint NOT NULL,
  CONSTRAINT `0` FOREIGN KEY (`artist_id`) REFERENCES `app1_musician` (`id`) ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- Create index "app1_album_artist_id_aed0987a" to table: "app1_album"
CREATE INDEX `app1_album_artist_id_aed0987a` ON `app1_album` (`artist_id`);
-- Create "app2_user" table
CREATE TABLE `app2_user` (
  `id` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `first_name` varchar NOT NULL,
  `last_name` varchar NULL,
  `roll` varchar NOT NULL
);
-- Create "app2_blog" table
CREATE TABLE `app2_blog` (
  `id` integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  `name` varchar NOT NULL,
  `created_at` date NOT NULL,
  `num_stars` integer NOT NULL,
  `author_id` bigint NOT NULL,
  CONSTRAINT `0` FOREIGN KEY (`author_id`) REFERENCES `app2_user` (`id`) ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- Create index "app2_blog_author_id_1675e606" to table: "app2_blog"
CREATE INDEX `app2_blog_author_id_1675e606` ON `app2_blog` (`author_id`);
