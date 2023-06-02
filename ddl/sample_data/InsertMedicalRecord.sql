USE [MedicalRecordDB]
GO

INSERT INTO [dbo].[MedicalRecord]
           ([PatientCode]
           ,[Date]
           ,[Record]
           ,[CreatedDateTime]
           ,[UpdatedDateTime]
           ,[IsDeleted])
     VALUES
           ('0000-123456'
           ,'2020-08-01'
           ,'FeNO 147 ppb'
           ,GETDATE()
           ,GETDATE()
           ,0),
           ('0000-123456'
           ,'2020-08-08'
           ,'FeNO 55 ppb'
           ,GETDATE()
           ,GETDATE()
           ,0),
           ('0000-123456'
           ,'2021-08-21'
           ,'FeNO 126 ppb'
           ,GETDATE()
           ,GETDATE()
           ,0)
GO


