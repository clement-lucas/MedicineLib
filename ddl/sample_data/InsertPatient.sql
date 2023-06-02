USE [MedicalRecordDB]
GO

INSERT INTO [dbo].[Patient]
           ([PatientCode]
           ,[Name]
           ,[CreatedDateTime]
           ,[UpdatedDateTime]
           ,[IsDeleted])
     VALUES
           ('0000-123456'
           ,N'鈴木 ヨシ子'
           ,GETDATE()
           ,GETDATE()
           ,0)
GO


