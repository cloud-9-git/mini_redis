#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./infra/create-ec2.sh <region> <ami-id> <key-name> <subnet-id> [docker-image] [bootstrap-only] [instance-type] [instance-name] [app-dir] [security-group-id] [vpc-id]

REGION="${1:?region required}"
AMI_ID="${2:?ami-id required}"
KEY_NAME="${3:?key-name required}"
SUBNET_ID="${4:?subnet-id required}"
DOCKER_IMAGE="${5:-auto}"
BOOTSTRAP_ONLY="${6:-true}"
INSTANCE_TYPE="${7:-t3.micro}"
INSTANCE_NAME="${8:-mini-redis-prod}"
APP_DIR="${9:-/opt/mini-redis}"
SECURITY_GROUP_ID="${10:-}"
VPC_ID="${11:-}"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI가 필요합니다." >&2
  exit 1
fi

if [[ -z "${SECURITY_GROUP_ID}" ]]; then
  if [[ -z "${VPC_ID}" ]]; then
    echo "security-group-id가 없으면 vpc-id가 필요합니다." >&2
    exit 1
  fi

  SG_NAME="mini-redis-sg-$(date +%s)"
  SECURITY_GROUP_ID="$(aws ec2 create-security-group \
    --region "${REGION}" \
    --group-name "${SG_NAME}" \
    --description "mini-redis security group" \
    --vpc-id "${VPC_ID}" \
    --query 'GroupId' \
    --output text)"

  aws ec2 authorize-security-group-ingress \
    --region "${REGION}" \
    --group-id "${SECURITY_GROUP_ID}" \
    --ip-permissions '[
      {"IpProtocol":"tcp","FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]},
      {"IpProtocol":"tcp","FromPort":8000,"ToPort":8000,"IpRanges":[{"CidrIp":"0.0.0.0/0"}]}
    ]' >/dev/null
fi

TMP_USER_DATA="$(mktemp)"
sed -e "s|__APP_DIR__|${APP_DIR}|g" \
    -e "s|__DOCKER_IMAGE__|${DOCKER_IMAGE}|g" \
    -e "s|__BOOTSTRAP_ONLY__|${BOOTSTRAP_ONLY}|g" \
    infra/user-data.sh > "${TMP_USER_DATA}"

INSTANCE_ID="$(aws ec2 run-instances \
  --region "${REGION}" \
  --image-id "${AMI_ID}" \
  --instance-type "${INSTANCE_TYPE}" \
  --key-name "${KEY_NAME}" \
  --subnet-id "${SUBNET_ID}" \
  --security-group-ids "${SECURITY_GROUP_ID}" \
  --user-data "file://${TMP_USER_DATA}" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${INSTANCE_NAME}}]" \
  --query 'Instances[0].InstanceId' \
  --output text)"

rm -f "${TMP_USER_DATA}"

echo "EC2 생성 완료: ${INSTANCE_ID}"
aws ec2 wait instance-running --region "${REGION}" --instance-ids "${INSTANCE_ID}"
PUBLIC_IP="$(aws ec2 describe-instances \
  --region "${REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)"

echo "Public IP: ${PUBLIC_IP}"
echo "Health URL: http://${PUBLIC_IP}:8000/v1/health"
echo "CD secrets:"
echo "  EC2_HOST=${PUBLIC_IP}"
echo "  EC2_USER=ubuntu"
echo "  EC2_APP_DIR=${APP_DIR}"
