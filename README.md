# Twitter Trend Analysis

## Architecture 
![Pipeline Architecture](/images/architecture.png)

#### Overview
The solution provides users a view of Twitter Trends and how they fared over a period of time. Users get to choose to see the Trends based on Country, Date as well as Top X (max top 50) trends. 

### Data Pipeline
#### Ingest Stage:
 - To pull data from Twitter, Twitter needs authentication keys i.e. API Key, API Secret Key, Access Token and Secret Access Token.
 - AWS Secrets Manager is used to store these keys.
 - First AWS Lambda function will read the keys from AWS Secrets Manager to pull the data from Twitter using Twitter API's. Data Collected from the Twitter API is ingested to Raw S3 folder.
 - The Data collected from Twitter is in JSON format.
 - Once the data is collected and ingested to Raw S3 folder a message is sent to AWS SQS Queue indicating the filename that the Transform job will use.
 
#### Transform Stage: 
 - Once AWS SQS Queue receives the filename from first Lambda function it triggers the Second AWS Lambda function indicating which file to pick and transform.
 - Second Lambda function will pick the file, processes and transforms it to CSV file with necessary information namely DateTime, Location, TrendName, TrendPosition and TweetVolume.
 - Once the transformation is completed the file is pushed to Tranformed S3 folder.
 
#### Data Dictionary
Below Data dictionary will be the outcome of Tranform Operation<br/>
**DateTime**      - *String*. Ex: 2020-12-28T12:08:00Z<br/>
**Location**      - *String*. Ex: Malaysia, Worldwide etc<br/>
**TrendName**     - *String*. Ex: Pandemic, Biden etc<br/>
**TrendPosition** - *Integer*. Ex: 1, 2, upto 50<br/>
**TrendVolume**   - *Integer*. Ex: 10000, 50000, etc<br/>

#### Visualization Stage:
 - The files from Tranform S3 folder is picked as and when received from Transform stage.
 - Visualization is refreshed automatically and reflect how Trend/Trends fared over a period of time.
 - User can choose to visualize trends based on specific Country, Date and Top X trends (max 50 Trends). For ex: Country:India, Date: 1st Jan 2021, Top 5 Trends.
 - Few visualizations are as shown below.
 
 <img src="/images/Top_5_Trends_Visualization-1.PNG" align="centre">
 <img src="/images/Top_10_Trends_Visualization-2.PNG" align="centre">
 <img src="/images/Top_10_Trends_Visualization-3.PNG" align="centre">
 <img src="/images/Top_10_Trends_Visualization-4.PNG" align="centre">

### Tools:
1. AWS Services: S3, SQS, Lambda Functions, Cloudwatch, Secrets Manager
2. Visualization: Plotly Dash
3. Language: Python
