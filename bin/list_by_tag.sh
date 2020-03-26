#!/bin/bash
tag_name=$1
tag_value=$2
if [ ! "$AWS_PROFILE" ]; then
    AWS_PROFILE=default
fi
if [ ! "$tag_value" ]; then
    tag_value=$tag_name
    tag_name=Name
fi

filter=Name=tag:$tag_name,Values=$tag_value

instanceids=$(aws ec2 describe-instances --filters $filter --output text --query 'Reservations[*].Instances[*].InstanceId' --profile $AWS_PROFILE)
if [ -z "$instanceids" ]; then
	echo Não há instanceids com tag $tag_name=$tag_value
    exit
fi
hostnames=$(aws ec2 describe-instances --instance-ids $instanceids --query='Reservations[*].Instances[*].PublicDnsName' --filters='Name=instance-state-name,Values=running' --output text --profile $AWS_PROFILE)
for host in $hostnames; do
    echo ubuntu@$host
done



