# 開発環境構築手順（新しく環境を作成する）

前提条件  
作業を行うための Azure サブスクリプションが存在する。  
作業者は上記に対して [Owner] または [ユーザー アクセス 管理者] の権限をもつ。  

1. ターミナルにてプロジェクトルートディレクトリーに移動する。  
cd <project_root>

2. 以下のコマンドを実行する。  
az login  
az account set -s <AZURE_SUBSCRIPTION_ID>  
AZURE_SUBSCRIPTION_ID には、対象の環境のサブスクリプションIDを入力する。  
  
3. 以下のコマンドを実行し、2で指定したサブスクリプションに切り替わっていることを確認する。  
az account show
  
4. 以下のコマンドを実行する。  
azd auth login  
azd env new <env_name>  
azd env select <env_name>  
  
5. 以下のコマンドを実行し、1で切り替えた環境の環境変数（./.azure/<env_name>/.env ファイルの設定内容）が表示されることを確認する。  
azd env get-values  
　 別の環境の環境変数が表示されたり、何も表示されなかったりする場合は、ターミナルを再起動し再度上記コマンドを実行して確認する。  
　 その際、最初にプロジェクトルートフォルダーへ移動する事を忘れないこと（cd <project_root>）  
  
6. 医療文献を登録用フォルダーに入れる。  
./data フォルダーに、 ./data_scanned の中身をコピーする。  
これにより、 azd up 時に pdf の内容が取り込まれる。  
一度取り込んだら、削除しておくこと。  
  
7. 以下のコマンドを実行する。  
azd init (もしも ERROR: environment already initialized to <env_name> というメッセージが出たら無視する)  
azd up  
location には **East US** or **South Central US** を指定する。
なお、使用可能な location は変更となる可能性がある。
  
8. 任意のデータベースを作成する。  
任意の RDB を作成する。  
作成したら、 ./ddl/ と ./ddl/sample_data/ 配下にある全ての sql ファイルを実行する。  
これらの SQL は Azure SQL Database 上で動作確認している。  
  
9. データベースの接続文字列を設定する。  
7のデータベースの接続文字列を設定する。  
./.azure/<env_name>/.env   
を開き、  
SQL_CONNECTION_STRING="<接続文字列>"  
を追記する。  
この設定は、 ./app/start.ps1 コマンドの実行によりローカル上でWebサーバー起動した際に参照される。  
  
次に、 Azure Portal 上でアプリケーション設定に接続文字列を追加する。  
  
【参照】  
https://learn.microsoft.com/ja-jp/azure/app-service/configure-common?tabs=portal#configure-app-settings  
  
この時、[アプリケーション設定]と[接続文字列]の設定カ所が存在するが、前者に対して設定する。  
  
名前：SQL_CONNECTION_STRING  
値：<接続文字列>  
  
10. 以降、システムに変更を加えた場合のデプロイに際しては、以下のコマンドを実行する。  
azd up  
ただし、 Web アプリケーションに対してのみ変更された場合は、以下のコマンドで良い。  
azd deploy  
  

# 開発環境構築手順（既に用意された環境で開発する）  
前提条件：  
環境、 <env_name> がすでに存在する。  
それぞれの環境の Azure 接続先が以下のファイルに記載してある。  
./.azure/<env_name>/.env  
  
以下の作業を開始する前、それぞれの環境のサブスクリプションやリソースグループに対しての作業者の権限を [Owner] のみ、あるいは [ユーザー アクセス 管理者] のみにしておく。  
  
参照元に追加したい pdf ファイルがある場合、./data/ フォルダー配下に配置する。  
pdf ファイルは暗号化されていない必要がある。  
  
  
1. ターミナルにてプロジェクトルートディレクトリーに移動する。  
cd <project_root>  
  
2. 以下のコマンドを実行する。  
az login  
az account set -s <AZURE_SUBSCRIPTION_ID>  
AZURE_SUBSCRIPTION_ID には、対象の環境のサブスクリプションIDを入力する。  
  
3. 以下のコマンドを実行し、2で指定したサブスクリプションに切り替わっていることを確認する。  
az account show
  
4. 以下のコマンドを実行する。  
azd auth login  
azd env select <env_name>  
  
5. 以下のコマンドを実行し、1で切り替えた環境の環境変数（./.azure/<env_name>/.env ファイルの設定内容）が表示されることを確認する。  
azd env get-values  
　 別の環境の環境変数が表示されたり、何も表示されなかったりする場合は、ターミナルを再起動し再度上記コマンドを実行して確認する。  
　 その際、最初にプロジェクトルートフォルダーへ移動する事を忘れないこと（cd <project_root>）  
  
6. 以下のコマンドを実行する。  
pwsh ./scripts/roles.ps1 （初回のみ）  
azd up  
  
7. 以降、システムに変更を加えた場合のデプロイに際しては、以下のコマンドを実行する。  
azd up  
ただし、 Web アプリケーションに対してのみ変更された場合は、以下のコマンドで良い。  
azd deploy  


# ローカルマシン上で Webサーバーを起動する  
ローカルマシン上で Webサーバーを起動するには以下のコマンドを実行する。  
./app ディレクトリに移動する。
./start.ps1 または ./start.sh を実行する。

# 医療文献を追加で読み込ませる
1. 医療文献を登録用フォルダーに入れる。  
./data フォルダーに、対象ファイルを入れる。  
一度取り込んだら、削除しておくこと。  

2. 以下のコマンドを実行する。  
cd <project_root>  
.\scripts\prepdocs.ps1  


# Azure SQL Server の認証に AAD 認証を使用する場合の手順
1. Azure Portal にアクセスし、Azure SQL Server の認証方式に AAD があることを確認する。  
  
2. Azure Portal にアクセスし、Azure SQL Server の アクセス制御 (IAM) にて、Web アプリケーションに SQL Server 共同管理者 権限を付与する。  

3. SQL データベースにて以下の SQL を実行する。  
.\ddl\credensial\CreateUser.sql  
この時、<web-app-name> の部分を、Web アプリケーションの名前に置き換える。  
  
4. 接続文字列を設定する。  
.azure\<env_name>\.env  
ファイルに以下の設定を記載する。  
<sql-server-namme>, <sql-db-namme> は適宜置き換える。  
この設定は、ローカルにて Webアプリケーションを実行する際に参照される。  
SQL_AUTHENTICATION="ActiveDirectoryMsi"  
SQL_CONNECTION_STRING="Driver={ODBC Driver 18 for SQL Server};Server=tcp:<sql-server-namme>.database.windows.net,1433;Database=<sql-db-name>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"  
同じ設定を、 Azure Portal 等から Web アプリケーションに対しても行う。  
この設定は、Azure 上にて Webアプリケーションを実行する際に参照される。  

# トラブルシューティング
## hogehoge.ps1 がロックされていて実行できない旨のエラーが発生
デプロイ作業中、 hogehoge.ps1 がロックされていて実行できない旨のエラーが発生した場合、power shell から以下のコマンドを実行し、ロックを解除し、再試行する。  
※：hogehoge の部分は適宜置き換わる。  

PS > Unblock-File -Path <file path>\hogehoge.ps1  


## RoleAssignmentExists: The role assignment already exists.が発生
デプロイ作業中、以下のようなエラーメッセージが発生した場合、サブスクリプションやリソースグループに対しての作業者の権限設定が合っていない可能性がある。  
作業者の権限を [Owner] のみ、あるいは [ユーザー アクセス 管理者] のみにすると解消する可能性がある。
  
ERROR: deployment failed: error deploying infrastructure: deploying to subscription:
  
Deployment Error Details:  
RoleAssignmentExists: The role assignment already exists.  
RoleAssignmentExists: The role assignment already exists.  
RoleAssignmentExists: The role assignment already exists.  
RoleAssignmentExists: The role assignment already exists.  
RoleAssignmentExists: The role assignment already exists.  
RoleAssignmentExists: The role assignment already exists.   
  
  
## $venvPythonPath へのファイルパスが見つからない旨のエラーメッセージが発生
script/prepdocs.ps1 内に記載された、python.exe へのパスを、作業者の環境に合わせて変更する。  
$venvPythonPath = "./scripts/.venv/scripts/python.exe"  


## azd env select {env_name} コマンドを実行しても環境が切り替わらない  
1. azd env select {env_name} コマンドを実行し、  
2. azd env get_values コマンドを実行すると、1で切り替えた環境の   
　 環境変数（./.azure/{env_name}/.env ファイルの設定内容）が表示されるはずであるが、
　 別の環境の環境変数が表示されたり、何も表示されなかったりする場合は、
　 VSCodeのターミナルではなく、OS上から新しい PowerShell ウィンドウを開き、
　 そちらで試す。
　 その際、最初にプロジェクトルートフォルダーへ移動する事を忘れないこと。
   cd {prj_root}


# ChatGPT + Enterprise data with Azure OpenAI and Cognitive Search

[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=599293758&machine=standardLinux32gb&devcontainer_path=.devcontainer%2Fdevcontainer.json&location=WestUs2)
[![Open in Remote - Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/azure-samples/azure-search-openai-demo)

This sample demonstrates a few approaches for creating ChatGPT-like experiences over your own data using the Retrieval Augmented Generation pattern. It uses Azure OpenAI Service to access the ChatGPT model (gpt-35-turbo), and Azure Cognitive Search for data indexing and retrieval.

The repo includes sample data so it's ready to try end to end. In this sample application we use a fictitious company called Contoso Electronics, and the experience allows its employees to ask questions about the benefits, internal policies, as well as job descriptions and roles.

![RAG Architecture](docs/appcomponents.png)

## Features

* Chat and Q&A interfaces
* Explores various options to help users evaluate the trustworthiness of responses with citations, tracking of source content, etc.
* Shows possible approaches for data preparation, prompt construction, and orchestration of interaction between model (ChatGPT) and retriever (Cognitive Search)
* Settings directly in the UX to tweak the behavior and experiment with options

![Chat screen](docs/chatscreen.png)

## Getting Started

> **IMPORTANT:** In order to deploy and run this example, you'll need an **Azure subscription with access enabled for the Azure OpenAI service**. You can request access [here](https://aka.ms/oaiapply). You can also visit [here](https://azure.microsoft.com/free/cognitive-search/) to get some free Azure credits to get you started.

> **AZURE RESOURCE COSTS** by default this sample will create Azure App Service and Azure Cognitive Search resources that have a monthly cost, as well as Form Recognizer resource that has cost per document page. You can switch them to free versions of each of them if you want to avoid this cost by changing the parameters file under the infra folder (though there are some limits to consider; for example, you can have up to 1 free Cognitive Search resource per subscription, and the free Form Recognizer resource only analyzes the first 2 pages of each document.)

### Prerequisites

#### To Run Locally
- [Azure Developer CLI](https://aka.ms/azure-dev/install)
- [Python 3+](https://www.python.org/downloads/)
    - **Important**: Python and the pip package manager must be in the path in Windows for the setup scripts to work.
    - **Important**: Ensure you can run `python --version` from console. On Ubuntu, you might need to run `sudo apt install python-is-python3` to link `python` to `python3`.    
- [Node.js](https://nodejs.org/en/download/)
- [Git](https://git-scm.com/downloads)
- [Powershell 7+ (pwsh)](https://github.com/powershell/powershell) - For Windows users only.
   - **Important**: Ensure you can run `pwsh.exe` from a PowerShell command. If this fails, you likely need to upgrade PowerShell.

>NOTE: Your Azure Account must have `Microsoft.Authorization/roleAssignments/write` permissions, such as [User Access Administrator](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#user-access-administrator) or [Owner](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#owner).  

#### To Run in GitHub Codespaces or VS Code Remote Containers

You can run this repo virtually by using GitHub Codespaces or VS Code Remote Containers.  Click on one of the buttons below to open this repo in one of those options.

[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=599293758&machine=standardLinux32gb&devcontainer_path=.devcontainer%2Fdevcontainer.json&location=WestUs2)
[![Open in Remote - Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/azure-samples/azure-search-openai-demo)

### Installation

#### Project Initialization

1. Create a new folder and switch to it in the terminal
1. Run `azd auth login`
1. Run `azd init -t azure-search-openai-demo`
    * For the target location, the regions that currently support the models used in this sample are **East US** or **South Central US**. For an up-to-date list of regions and models, check [here](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models)

#### Starting from scratch:

Execute the following command, if you don't have any pre-existing Azure services and want to start from a fresh deployment.

1. Run `azd up` - This will provision Azure resources and deploy this sample to those resources, including building the search index based on the files found in the `./data` folder.
1. After the application has been successfully deployed you will see a URL printed to the console.  Click that URL to interact with the application in your browser.  

It will look like the following:

!['Output from running azd up'](assets/endpoint.png)
    
> NOTE: It may take a minute for the application to be fully deployed. If you see a "Python Developer" welcome screen, then wait a minute and refresh the page.

#### Use existing resources:

1. Run `azd env set AZURE_OPENAI_SERVICE {Name of existing OpenAI service}`
1. Run `azd env set AZURE_OPENAI_RESOURCE_GROUP {Name of existing resource group that OpenAI service is provisioned to}`
1. Run `azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT {Name of existing ChatGPT deployment}`. Only needed if your ChatGPT deployment is not the default 'chat'.
1. Run `azd env set AZURE_OPENAI_GPT_DEPLOYMENT {Name of existing GPT deployment}`. Only needed if your ChatGPT deployment is not the default 'chat'.
1. Run `azd up`

> NOTE: You can also use existing Search and Storage Accounts.  See `./infra/main.parameters.json` for list of environment variables to pass to `azd env set` to configure those existing resources.

#### Deploying or re-deploying a local clone of the repo:
* Simply run `azd up`

#### Running locally:
1. Run `azd login`
2. Change dir to `app`
3. Run `./start.ps1` or `./start.sh` or run the "VS Code Task: Start App" to start the project locally.

#### Sharing Environments

Run the following if you want to give someone else access to completely deployed and existing environment.

1. Install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
1. Run `azd init -t azure-search-openai-demo`
1. Run `azd env refresh -e {environment name}` - Note that they will need the azd environment name, subscription Id, and location to run this command - you can find those values in your `./azure/{env name}/.env` file.  This will populate their azd environment's .env file with all the settings needed to run the app locally.
1. Run `pwsh ./scripts/roles.ps1` - This will assign all of the necessary roles to the user so they can run the app locally.  If they do not have the necessary permission to create roles in the subscription, then you may need to run this script for them. Just be sure to set the `AZURE_PRINCIPAL_ID` environment variable in the azd .env file or in the active shell to their Azure Id, which they can get with `az account show`.

### Quickstart

* In Azure: navigate to the Azure WebApp deployed by azd. The URL is printed out when azd completes (as "Endpoint"), or you can find it in the Azure portal.
* Running locally: navigate to 127.0.0.1:5000

Once in the web app:
* Try different topics in chat or Q&A context. For chat, try follow up questions, clarifications, ask to simplify or elaborate on answer, etc.
* Explore citations and sources
* Click on "settings" to try different options, tweak prompts, etc.

## Resources

* [Revolutionize your Enterprise Data with ChatGPT: Next-gen Apps w/ Azure OpenAI and Cognitive Search](https://aka.ms/entgptsearchblog)
* [Azure Cognitive Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
* [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/overview)

### Note
>Note: The PDF documents used in this demo contain information generated using a language model (Azure OpenAI Service). The information contained in these documents is only for demonstration purposes and does not reflect the opinions or beliefs of Microsoft. Microsoft makes no representations or warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability or availability with respect to the information contained in this document. All rights reserved to Microsoft.

### FAQ

***Question***: Why do we need to break up the PDFs into chunks when Azure Cognitive Search supports searching large documents?

***Answer***: Chunking allows us to limit the amount of information we send to OpenAI due to token limits. By breaking up the content, it allows us to easily find potential chunks of text that we can inject into OpenAI. The method of chunking we use leverages a sliding window of text such that sentences that end one chunk will start the next. This allows us to reduce the chance of losing the context of the text.

### Troubleshooting

If you see this error while running `azd deploy`: `read /tmp/azd1992237260/backend_env/lib64: is a directory`, then delete the `./app/backend/backend_env folder` and re-run the `azd deploy` command.  This issue is being tracked here: https://github.com/Azure/azure-dev/issues/1237

If the web app fails to deploy and you receive a '404 Not Found' message in your browser, run 'azd deploy'. 


