#!/bin/bash

REGION=$1

if [[ "$REGION" == "" ]];
then
	echo "ERROR: must provide AWS region code as argument to script"
	exit
fi


if [[ ! -e yaml/${REGION}/vpc.yaml ]];
then
	echo "ERROR: yaml/${REGION}/vpc.yaml is not setup yet"
	exit;
fi

if [[ ! -e params/${REGION}/af-vpc-parameters.json ]];
then
	echo "ERROR: params/${REGION}/af-vpc-parameters.json is not setup yet"
	exit;
fi


aws cloudformation create-stack --stack-name af-vpc \
--template-body file://yaml/${REGION}/vpc.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters file://params/${REGION}/af-vpc-parameters.json \
--region ${REGION}

