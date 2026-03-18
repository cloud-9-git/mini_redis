# EC2 자동 생성/배포 가이드

## 무엇이 자동화되나

- EC2 인스턴스 생성
- 보안 그룹(옵션) 자동 생성
- 인스턴스 최초 부팅 시 `user-data` 자동 실행
  - Docker/Compose 설치
  - `docker-compose.yml`/`.env` 생성
  - 서버 상태 점검 후 필요한 설정만 반영(idempotent)
  - 옵션에 따라 앱 실행까지 수행

## 사전 준비 (인증/권한)

- 로컬에 AWS CLI 설치
- AWS 자격 증명 설정 (`aws configure` 또는 환경 변수)
- IAM 권한(최소):
  - `ec2:RunInstances`
  - `ec2:DescribeInstances`
  - `ec2:CreateSecurityGroup`
  - `ec2:AuthorizeSecurityGroupIngress`
  - `ec2:CreateTags`
  - `ec2:Wait`
- SSH 접속용 Key Pair 미리 생성

## Windows (PowerShell) 실행

```powershell
.\infra\create-ec2.ps1 `
  -Region ap-northeast-2 `
  -AmiId ami-xxxxxxxx `
  -KeyName my-keypair `
  -SubnetId subnet-xxxxxxxx `
  -VpcId vpc-xxxxxxxx `
  -DockerImage auto `
  -BootstrapOnly $true
```

이미 만들어둔 보안그룹을 쓰면 `-SecurityGroupId sg-xxxx`를 넣고 `-VpcId`는 생략할 수 있습니다.

- `-DockerImage auto -BootstrapOnly $true`: 서버 기초 세팅만 수행(권장)
- `-DockerImage your-id/mini-redis:latest -BootstrapOnly $false`: 최초 생성 시 앱까지 즉시 실행

## Linux/macOS 실행

```bash
chmod +x infra/create-ec2.sh
./infra/create-ec2.sh \
  ap-northeast-2 \
  ami-xxxxxxxx \
  my-keypair \
  subnet-xxxxxxxx \
  auto \
  true \
  t3.micro \
  mini-redis-prod \
  /opt/mini-redis \
  "" \
  vpc-xxxxxxxx
```

## 생성 후 GitHub Actions CD 연결

스크립트 출력값으로 아래 시크릿을 등록하세요.

- `EC2_HOST`
- `EC2_USER` (`ubuntu`)
- `EC2_APP_DIR` (기본 `/opt/mini-redis`)

추가로 아래 시크릿도 필요합니다.

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `EC2_SSH_KEY` (PEM 개인키 본문)
