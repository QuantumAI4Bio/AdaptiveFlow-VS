#!/bin/bash

REGION=$1

if [[ "$REGION" == "" ]];
then
	echo "ERROR: must provide AWS region code as argument to script"
	exit
fi


if [[ ! -e yaml/af.yaml ]];
then
	echo "ERROR: yaml/af.yaml is not setup yet"
	exit;
fi

if [[ ! -e params/${REGION}/af-parameters.json ]];
then
	echo "ERROR: params/${REGION}/af-parameters.json is not setup yet"
	exit;
fi


aws cloudformation create-stack --stack-name af \
--template-body file://yaml/af.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters file://params/${REGION}/af-parameters.json \
--region ${REGION}

