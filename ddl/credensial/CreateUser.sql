-- 以下は、 SQL Server の認証に AAD を使用する場合、このクエリを実行してください。
-- <web-app-name> の部分を、Web アプリケーションの名前に置き換えてください。
-- SQL Server の認証に SQL 認証を用いる場合は、実行は必要ありません。
CREATE USER [<web-app-name>] FROM EXTERNAL PROVIDER
ALTER ROLE db_datareader ADD MEMBER [<web-app-name>]
ALTER ROLE db_datawriter ADD MEMBER [<web-app-name>]