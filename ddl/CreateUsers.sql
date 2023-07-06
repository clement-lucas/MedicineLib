CREATE TABLE Users (
    UserId VARCHAR(50) NOT NULL,
    UserName VARCHAR(10),
	CreatedDateTime [datetime] NULL,
	UpdatedDateTime [datetime] NULL,
	IsDeleted [bit] NULL
);