#!/bin/bash
set -eu

 
#=========================================================================================================================
# setup variables
#=========================================================================================================================
appName="qualys-jira-integration"
bucketName="gc-$appName"
octopusProjectName="Lambda - Qualys to Jira"

echo "s3 bucket name: $bucketName"

#=========================================================================================================================
# create s3 bucket if it does not exist
#=========================================================================================================================
if aws s3 ls "s3://$bucketName" 2>&1 | grep -q 'NoSuchBucket'
then 
	echo "creating bucket: $bucketName"
	aws s3 mb s3://$bucketName 
fi

# apply bucket policies
aws s3api put-bucket-policy --bucket $bucketName --policy file://bucket-policy.json


#=========================================================================================================================
# build application based on the sam template.yaml
#=========================================================================================================================
sam build --build-dir deploy

#=========================================================================================================================
# package the build output into a zip file and upload to s3
#=========================================================================================================================
sam package --template-file deploy/template.yaml --s3-bucket $bucketName --output-template-file package.yml --region us-east-1

#=========================================================================================================================
# AWS: get the current build number of the api from the parameter store and increment
#=========================================================================================================================
buildNumber=$(aws ssm get-parameters --names "/gc-internal/$appName/buildNumber" | jq '.Parameters[0].Value'  | tr -d '"')

# buildNumber will be "null" if this is the first time the build is running
if [[ $buildNumber == "null" ]]; then buildNumber="0"; fi

newBuildNumber=$(expr $buildNumber + 1)

major="0"
minor="1"
patch="0"
fullVersion=$major.$minor.$patch.$newBuildNumber

echo "version to be built: $fullVersion"

aws ssm put-parameter --name "/gc-internal/$appName/buildNumber" --value $newBuildNumber --type String --overwrite
echo "updated  parameter store with version... $newBuildNumber"

#=========================================================================================================================
# package the build output into a zip file and upload to s3
#=========================================================================================================================
zip gc-$appName-package.$fullVersion.zip package.yml

#=========================================================================================================================
# GIT:  Tagging this commit with the build number
#========================================================================================================================= 
# Environment variable containing the SHA of the last commit.  AWS gives us this env var, ie. we don't set this
#echo "SHA of last commit"
#echo $CODEBUILD_RESOLVED_SOURCE_VERSION

# adding $fullVersion as the tag
#curl -u $GITHUB_USER:$GITHUB_TOKEN -H "Content-Type: application/json" -g -d "{ \"ref\": \"refs/tags/$fullVersion\", \"sha\": \"$CODEBUILD_RESOLVED_SOURCE_VERSION\" }" #https://api.github.com/repos/Geo-Comm/gc-indoormap-create-rooms-prep/git/refs

#=========================================================================================================================
# OCTOPUS: Push package (zip file) to octopus.
#=========================================================================================================================
echo "uploading package to octopus..."
dotnet octo push --package=gc-$appName-package.$fullVersion.zip --overwrite-mode=OverwriteExisting --server https://geocomm.octopus.app/ --apiKey $OCTOPUS_API_KEY --ignoreSslErrors

#=========================================================================================================================
# OCTOPUS:  Create release in Octopus.
#========================================================================================================================= 
echo "creating release"
dotnet octo create-release --project "$octopusProjectName" --version $fullVersion --server https://geocomm.octopus.app/ --apiKey $OCTOPUS_API_KEY --deployto=Dev --ignoreSslErrors