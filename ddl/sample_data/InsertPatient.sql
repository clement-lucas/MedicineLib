USE [MedicalRecordDB]
GO

INSERT INTO [dbo].[Patient]
           ([PatientCode]
           ,[Name]
           ,[CreatedDateTime]
           ,[UpdatedDateTime]
           ,[IsDeleted])
     VALUES
           ('0000-000001'
           ,N'鈴木 ヨシ子'
           ,GETDATE()
           ,GETDATE()
           ,0)
           ,
            ('0000-000002'
           ,N'佐藤 太郎'
           ,GETDATE()
           ,GETDATE()
           ,0)
           ,
            ('0000-000004'
           ,N'鈴木 美香'
           ,GETDATE()
           ,GETDATE()
           ,0)

GO


