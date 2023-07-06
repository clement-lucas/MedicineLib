CREATE TABLE History (
    Id INT NOT NULL IDENTITY,
    UserId VARCHAR(50) NOT NULL,
    PID VARCHAR(10),  
    DocumentName NVARCHAR(50) NOT NULL,
    Prompt NVARCHAR(max) NOT NULL,
    MedicalRecord NVARCHAR(max) NOT NULL,
    Response NVARCHAR(max) NOT NULL,
	CreatedDateTime [datetime] NULL,
	UpdatedDateTime [datetime] NULL,
	IsDeleted [bit] NULL
    PRIMARY KEY (Id)
);