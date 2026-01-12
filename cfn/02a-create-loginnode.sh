#!/bin/bash

REGION=$1

if [[ "$REGION" == "" ]];
then
	echo "ERROR: must provide AWS region code as argument to script"
	exit
fi


if [[ ! -e yaml/af-loginnode.yaml ]];
then
	echo "ERROR: yaml/af-loginnode.yaml is not setup yet"
	exit;
fi

if [[ ! -e params/${REGION}/af-loginnode-parameters.json ]];
then
	echo "ERROR: params/${REGION}/af-loginnode-parameters.json is not setup yet"
	exit;
fi


aws cloudformation create-stack --stack-name af-loginnode \
--template-body file://yaml/af-loginnode.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters file://params/${REGION}/af-loginnode-parameters.json \
--region ${REGION}

