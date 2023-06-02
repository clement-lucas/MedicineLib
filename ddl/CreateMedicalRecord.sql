/****** Object:  Table [dbo].[MedicalRecord]    Script Date: 2023/06/02 9:40:20 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[MedicalRecord](
	[PatientCode] [char](32) NOT NULL,
	[Date] [date] NULL,
	[Record] [nvarchar](MAX) NULL,
	[CreatedDateTime] [datetime] NULL,
	[UpdatedDateTime] [datetime] NULL,
	[IsDeleted] [bit] NULL
) ON [PRIMARY]
GO


