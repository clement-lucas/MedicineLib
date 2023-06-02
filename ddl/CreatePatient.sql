/****** Object:  Table [dbo].[Patient]    Script Date: 2023/06/01 9:09:41 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Patient](
	[PatientCode] [char](32) NOT NULL,
	[Name] [nchar](32) NOT NULL,
	[CreatedDateTime] [datetime] NULL,
	[UpdatedDateTime] [datetime] NULL,
	[IsDeleted] [bit] NULL,
	CONSTRAINT AK_PatientCode UNIQUE(PatientCode)  
) ON [PRIMARY]
GO


