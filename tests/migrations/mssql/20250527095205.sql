-- Create "app1_musician" table
CREATE TABLE [app1_musician] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [first_name] nvarchar(50) NOT NULL,
  [last_name] nvarchar(50) NOT NULL,
  [instrument] nvarchar(100) NOT NULL,
  CONSTRAINT [PK__app1_mus__3213E83FF9084924] PRIMARY KEY CLUSTERED ([id] ASC)
);
-- Create "app1_album" table
CREATE TABLE [app1_album] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [name] nvarchar(100) NOT NULL,
  [release_date] date NOT NULL,
  [num_stars] int NOT NULL,
  [artist_id] bigint NOT NULL,
  CONSTRAINT [PK__app1_alb__3213E83F79D58D92] PRIMARY KEY CLUSTERED ([id] ASC),
  CONSTRAINT [app1_album_artist_id_aed0987a_fk_app1_musician_id] FOREIGN KEY ([artist_id]) REFERENCES [app1_musician] ([id]) ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- Create index "app1_album_artist_id_aed0987a" to table: "app1_album"
CREATE NONCLUSTERED INDEX [app1_album_artist_id_aed0987a] ON [app1_album] ([artist_id] ASC);
-- Create "app2_user" table
CREATE TABLE [app2_user] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [first_name] nvarchar(50) NOT NULL,
  [last_name] nvarchar(50) NULL,
  [roll] nvarchar(100) NOT NULL,
  CONSTRAINT [PK__app2_use__3213E83F9487A488] PRIMARY KEY CLUSTERED ([id] ASC)
);
-- Create "app2_blog" table
CREATE TABLE [app2_blog] (
  [id] bigint IDENTITY (1, 1) NOT NULL,
  [name] nvarchar(100) NOT NULL,
  [created_at] date NOT NULL,
  [num_stars] int NOT NULL,
  [author_id] bigint NOT NULL,
  CONSTRAINT [PK__app2_blo__3213E83FC1FC503A] PRIMARY KEY CLUSTERED ([id] ASC),
  CONSTRAINT [app2_blog_author_id_1675e606_fk_app2_user_id] FOREIGN KEY ([author_id]) REFERENCES [app2_user] ([id]) ON UPDATE NO ACTION ON DELETE NO ACTION
);
-- Create index "app2_blog_author_id_1675e606" to table: "app2_blog"
CREATE NONCLUSTERED INDEX [app2_blog_author_id_1675e606] ON [app2_blog] ([author_id] ASC);
