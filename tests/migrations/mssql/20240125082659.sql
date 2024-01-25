-- Create "app1_musician" table
CREATE TABLE [app1_musician] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [first_name] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  [last_name] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  [instrument] nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  CONSTRAINT [PK_app1_musician] PRIMARY KEY CLUSTERED ([id] ASC)
);
-- Create "app1_album" table
CREATE TABLE [app1_album] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [name] nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  [release_date] date NOT NULL,
  [num_stars] int NOT NULL,
  [artist_id] bigint NOT NULL,
  CONSTRAINT [PK_app1_album] PRIMARY KEY CLUSTERED ([id] ASC),
 
  CONSTRAINT [app1_album_artist_id_aed0987a_fk_app1_musician_id] FOREIGN KEY ([artist_id]) REFERENCES [app1_musician] ([id]) ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- Create index "app1_album_artist_id_aed0987a" to table: "app1_album"
CREATE NONCLUSTERED INDEX [app1_album_artist_id_aed0987a] ON [app1_album] ([artist_id] ASC);
-- Create "app2_user" table
CREATE TABLE [app2_user] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [first_name] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  [last_name] nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
  [roll] nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  CONSTRAINT [PK_app2_user] PRIMARY KEY CLUSTERED ([id] ASC)
);
-- Create "app2_blog" table
CREATE TABLE [app2_blog] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [name] nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
  [created_at] date NOT NULL,
  [num_stars] int NOT NULL,
  [author_id] bigint NOT NULL,
  CONSTRAINT [PK_app2_blog] PRIMARY KEY CLUSTERED ([id] ASC),
 
  CONSTRAINT [app2_blog_author_id_1675e606_fk_app2_user_id] FOREIGN KEY ([author_id]) REFERENCES [app2_user] ([id]) ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- Create index "app2_blog_author_id_1675e606" to table: "app2_blog"
CREATE NONCLUSTERED INDEX [app2_blog_author_id_1675e606] ON [app2_blog] ([author_id] ASC);
