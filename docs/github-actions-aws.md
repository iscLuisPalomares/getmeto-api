# GitHub Actions deployment to ECR and EKS

The workflow at [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) deploys every push to `main`. Protect `main` so changes arrive through merged pull requests; that makes a merge the only normal deployment trigger. The workflow creates an immutable image tag from the first 12 characters of the merge commit SHA, pushes it to ECR, applies the Kubernetes manifests, and waits up to five minutes for the rollout.

It uses GitHub Actions OpenID Connect (OIDC), not an AWS access key stored as a GitHub secret.

## One-time AWS setup

Substitute your account, GitHub organization, repository, Region, ECR repository, EKS cluster, and deployment IAM role names below.

1. Create the ECR repository if it does not already exist. Enable immutable tags and scan-on-push.
2. Create an IAM OIDC provider for `https://token.actions.githubusercontent.com` in the AWS account if one does not already exist.
3. Create a dedicated deployment IAM role with this trust policy. This workflow uses GitHub's `production` environment, so `sub` must reference that environment. Configure that environment to allow deployments only from `main`; GitHub then prevents other branches from requesting this role.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:<GITHUB_ORGANIZATION>/<REPOSITORY>:environment:production"
      }
    }
  }]
}
```

For repositories that use GitHub's immutable OIDC subject claims, use the owner and repository ID format shown in GitHub's OIDC documentation instead of the name-based `sub` above. Do not loosen this condition to a wildcard.

4. Grant that role the minimum permissions to push to the specific ECR repository, describe the EKS cluster, and access Kubernetes through an EKS access entry. The role needs `ecr:GetAuthorizationToken` on `*`, and `ecr:BatchCheckLayerAvailability`, `ecr:CompleteLayerUpload`, `ecr:InitiateLayerUpload`, `ecr:PutImage`, and `ecr:UploadLayerPart` on the ECR repository ARN.
5. Create an EKS access entry for the deployment role and associate a namespace-scoped policy. For an initial deployment to the current `default` namespace:

```bash
aws eks create-access-entry \
  --cluster-name <EKS_CLUSTER_NAME> \
  --principal-arn <DEPLOYMENT_ROLE_ARN> \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name <EKS_CLUSTER_NAME> \
  --principal-arn <DEPLOYMENT_ROLE_ARN> \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy \
  --access-scope type=namespace,namespaces=default
```

For production, create an application namespace and scope this access policy to it instead of `default`. Replace the broad EKS admin policy with Kubernetes RBAC tailored to the Deployment, Service, and ConfigMap once the initial path works.

The EKS **node** IAM role separately needs `AmazonEC2ContainerRegistryPullOnly` so the nodes can pull private ECR images. The GitHub deployment role is not used by running Pods.

## GitHub repository configuration

Create these GitHub Actions repository variables under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Example |
| --- | --- |
| `AWS_REGION` | `us-east-1` |
| `AWS_ROLE_TO_ASSUME` | `arn:aws:iam::<ACCOUNT_ID>:role/getmeto-api-github-deploy` |
| `ECR_REPOSITORY` | `myapps/getmeto` |
| `EKS_CLUSTER_NAME` | Your EKS cluster name |
| `KUBERNETES_NAMESPACE` | `default` (optional) |

Create the GitHub `production` environment, restrict its deployment branches to `main`, and optionally require an approval before deployment. Do not store AWS access keys in GitHub secrets.

## Deployment behavior

The workflow renders a temporary copy of `k8s/` and replaces the Kustomize image name and tag there. It deliberately does not commit the resulting tag back to `main`; the GitHub Actions run is the deployment record. The build targets `linux/amd64`, which matches typical EKS managed node groups. If you use ARM-based EKS nodes, change the platform to `linux/arm64`; use a multi-platform build if both are needed.
