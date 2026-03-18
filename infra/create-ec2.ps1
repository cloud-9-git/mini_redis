param(
  [Parameter(Mandatory = $true)]
  [string]$Region,

  [Parameter(Mandatory = $true)]
  [string]$AmiId,

  [Parameter(Mandatory = $true)]
  [string]$KeyName,

  [Parameter(Mandatory = $true)]
  [string]$SubnetId,

  [string]$DockerImage = "auto",
  [bool]$BootstrapOnly = $true,

  [string]$InstanceType = "t3.micro",
  [string]$InstanceName = "mini-redis-prod",
  [string]$AppDir = "/opt/mini-redis",
  [string]$VpcId = "",
  [string]$SecurityGroupId = "",
  [string]$IamInstanceProfileName = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$AwsCliPath = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"

function Invoke-Aws {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
  & $AwsCliPath @Args
}

function Require-AwsCli {
  if (-not (Test-Path $AwsCliPath)) {
    throw "AWS CLI가 설치되어 있지 않습니다. 먼저 설치하세요."
  }
  Invoke-Aws --version | Out-Null
}

function New-SecurityGroupIfNeeded {
  param(
    [string]$RegionParam,
    [string]$VpcIdParam,
    [string]$ExistingSecurityGroupId
  )

  if ($ExistingSecurityGroupId -ne "") {
    return $ExistingSecurityGroupId
  }

  if ($VpcIdParam -eq "") {
    throw "SecurityGroupId를 직접 넣지 않는 경우 VpcId가 필요합니다."
  }

  $groupName = "mini-redis-sg-$([int](Get-Date -UFormat %s))"
  $sgId = Invoke-Aws ec2 create-security-group `
    --region $RegionParam `
    --group-name $groupName `
    --description "mini-redis security group" `
    --vpc-id $VpcIdParam `
    --query "GroupId" `
    --output text

  Invoke-Aws ec2 authorize-security-group-ingress `
    --region $RegionParam `
    --group-id $sgId `
    --protocol tcp `
    --port 22 `
    --cidr 0.0.0.0/0 | Out-Null

  Invoke-Aws ec2 authorize-security-group-ingress `
    --region $RegionParam `
    --group-id $sgId `
    --protocol tcp `
    --port 8000 `
    --cidr 0.0.0.0/0 | Out-Null

  return $sgId.Trim()
}

Require-AwsCli

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$userDataTemplatePath = Join-Path $scriptDir "user-data.sh"
$userDataTemplate = Get-Content -Raw $userDataTemplatePath
$bootstrapOnlyValue = if ($BootstrapOnly) { "true" } else { "false" }
$finalUserData = $userDataTemplate.
  Replace("__APP_DIR__", $AppDir).
  Replace("__DOCKER_IMAGE__", $DockerImage).
  Replace("__BOOTSTRAP_ONLY__", $bootstrapOnlyValue)

$tmpUserDataPath = Join-Path $env:TEMP "mini-redis-user-data-$(Get-Random).sh"
Set-Content -Path $tmpUserDataPath -Value $finalUserData -NoNewline

try {
  $sgId = New-SecurityGroupIfNeeded -RegionParam $Region -VpcIdParam $VpcId -ExistingSecurityGroupId $SecurityGroupId

  $tagSpec = "ResourceType=instance,Tags=[{Key=Name,Value=$InstanceName}]"
  $runArgs = @(
    "ec2", "run-instances",
    "--region", $Region,
    "--image-id", $AmiId,
    "--instance-type", $InstanceType,
    "--key-name", $KeyName,
    "--subnet-id", $SubnetId,
    "--security-group-ids", $sgId,
    "--user-data", "file://$tmpUserDataPath",
    "--tag-specifications", $tagSpec,
    "--query", "Instances[0].InstanceId",
    "--output", "text"
  )

  if ($IamInstanceProfileName -ne "") {
    $runArgs += @("--iam-instance-profile", "Name=$IamInstanceProfileName")
  }

  $instanceId = Invoke-Aws @runArgs
  $instanceId = $instanceId.Trim()

  Write-Host "EC2 생성 완료: $instanceId"
  Write-Host "인스턴스 실행 대기중..."
  Invoke-Aws ec2 wait instance-running --region $Region --instance-ids $instanceId

  $publicIp = Invoke-Aws ec2 describe-instances `
    --region $Region `
    --instance-ids $instanceId `
    --query "Reservations[0].Instances[0].PublicIpAddress" `
    --output text

  Write-Host "Public IP: $publicIp"
  Write-Host "Health URL: http://$publicIp`:8000/v1/health"
  Write-Host "CD 시크릿용:"
  Write-Host "  EC2_HOST=$publicIp"
  Write-Host "  EC2_USER=ubuntu"
  Write-Host "  EC2_APP_DIR=$AppDir"
}
finally {
  if (Test-Path $tmpUserDataPath) {
    Remove-Item $tmpUserDataPath -Force
  }
}
