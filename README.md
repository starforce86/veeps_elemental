# Veeps_Elemental

Set of APIs and Terraform IaC to bring up a streaming platform on AWS using AWS's managed service for video streaming (AWS Elemental)

## 1. How do I get set up? 

### 1.1. Summary of set up

#### Backend

Install [Docker version 20.10.17](https://docker.com) and [docker-compose v.2.6.1](https://docs.docker.com/compose/install/)

1. Copy the environment file by running `cp .env.template .env`
2. Run `docker-compose up -d` and it will build and run the project.

##### See [BACKEND README](apps/veepsapi/README.md) for more specific information about the backend.

#### Frontend
(TBD...)


#### AWS credentials
If you are using 2FA to access AWS, you need to get an access token that is valid for a maximum of 36 hours.

##### AWS CLI:
To acquire the STS token, run the following commands (append `--profile {{ profile name }}` if you are using a non-default AWS profile):
1. Run `aws iam list-mfa-devices` to get the ARN of the MFA device.
2. Run `aws sts get-session-token --duration-seconds 129600 --serial-number {{ MFA ARN from above }} --token-code {{ code from MFA device }}`
3. Copy the relevant info into your local `.env` file.

example:
```shell
aws iam list-mfa-devices --profile veeps
{
    "MFADevices": [
        {
            "UserName": "steve.butler",
            "SerialNumber": "arn:aws:iam::695729695688:mfa/steve.butler",
            "EnableDate": "DATEMFADEVICEENABLED"
        }
    ]
}

aws sts get-session-token --duration-seconds 129600 --serial-number arn:aws:iam::695729695688:mfa/steve.butler --profile veeps --token-code 123456
{
    "Credentials": {
        "AccessKeyId": "ASIARANDOMACCESSKEY",
        "SecretAccessKey": "SUPERSECRETACCESSKEYWITHSTUFF",
        "SessionToken": "REALLYLONGTOKENTHATWILLHELPAUTHENTICATE",
        "Expiration": "DATE3DAYSFROMREQUEST"
    }
}

```

# Deployments/branches
| Branch          | Pipeline trigger   |
|-----------------|--------------------|
| **develop**     | deploy on PR merge |
| **staging**     | deploy on PR merge | 
| **production**  | deploy on PR merge | 

