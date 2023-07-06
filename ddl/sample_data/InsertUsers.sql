USE [MedicalRecordDB]
GO

INSERT INTO [dbo].[Users]
           ([UserId]
           ,[UserName]
           ,[CreatedDateTime]
           ,[UpdatedDateTime]
           ,[IsDeleted])
     VALUES
           ('000001'
           ,'阿部 潤子'
           ,GETDATE()
           ,GETDATE()
           ,0)
GO


