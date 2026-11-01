# 6. Google Cloud setup (one time)

Do every step once for **staging** and once for **production**. The examples use production; for staging, change the project ID and use smaller sizes where noted.

You need:
- The [gcloud CLI](https://cloud.google.com/sdk/docs/install), logged in with `gcloud auth login`.
- Owner rights on the project.
- The Firebase steps 1–2 from [Firebase setup](04-firebase-setup.md) done first. That creates the project and turns on billing.

Copy this block into your terminal first and adjust the values:

```bash
export PROJECT_ID=college-prod                 # or college-staging
export REGION=asia-south1                      # Mumbai
export GITHUB_REPO=your-org/college-backend
gcloud config set project "$PROJECT_ID"
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
```

## 1. What you are creating

| Resource | Name | Purpose |
|---|---|---|
| Artifact Registry repository | `college` | Stores container images |
| Cloud SQL instance | `college-db` (PostgreSQL 16) | The database |
| Database / user | `college` / `college_app` | App database and login |
| Secrets | `college-db-password`, `college-exam-token-secret` | Passwords and keys |
| Service account | `college-api` | Identity of the running backend |
| Service account | `college-scheduler` | Identity used by Cloud Scheduler |
| Service account | `college-deployer` | Identity used by GitHub Actions to deploy |
| Workload Identity pool | `github` | Lets GitHub Actions log in without keys |
| Scheduler job | `college-lead-sync` | Retries Google Sheets rows every 5 minutes |

## 2. Turn on the required Google services

```bash
gcloud services enable run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com cloudscheduler.googleapis.com iam.googleapis.com iamcredentials.googleapis.com \
  sts.googleapis.com sheets.googleapis.com identitytoolkit.googleapis.com firebaseappcheck.googleapis.com \
  storage.googleapis.com logging.googleapis.com monitoring.googleapis.com
```

## 3. Container registry

```bash
gcloud artifacts repositories create college --repository-format=docker --location="$REGION" \
  --description="College backend images"
```

## 4. Database (Cloud SQL for PostgreSQL)

**Production** uses a small dedicated machine with daily backups and point-in-time recovery:

```bash
gcloud sql instances create college-db --database-version=POSTGRES_16 --region="$REGION" \
  --edition=ENTERPRISE --tier=db-custom-1-3840 --storage-size=20GB --storage-auto-increase \
  --backup-start-time=20:30 --enable-point-in-time-recovery --retained-backups-count=14 \
  --retained-transaction-log-days=7 --maintenance-window-day=SUN --maintenance-window-hour=21 \
  --deletion-protection
```

Notes:
- Times are UTC: 20:30 UTC is 02:00 IST (backup); Sunday 21:00 UTC is Monday 02:30 IST (maintenance).
- **Staging** can use the cheapest shared machine: `db-f1-micro`, and drop `--deletion-protection` if you like.
- For automatic failover to a second zone, add `--availability-type=REGIONAL`. It roughly doubles the database cost.

Create the database and the application user. The password is generated and saved straight into Secret Manager in the next step:

```bash
gcloud sql databases create college --instance=college-db
export DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)
gcloud sql users create college_app --instance=college-db --password="$DB_PASSWORD"
```

## 5. Secrets

```bash
printf '%s' "$DB_PASSWORD" | gcloud secrets create college-db-password --replication-policy=automatic --data-file=-
openssl rand -hex 32 | tr -d '\n' | gcloud secrets create college-exam-token-secret --replication-policy=automatic --data-file=-
unset DB_PASSWORD
```

## 6. Service accounts and permissions

```bash
gcloud iam service-accounts create college-api --display-name="College API (Cloud Run)"
gcloud iam service-accounts create college-scheduler --display-name="College Cloud Scheduler"
gcloud iam service-accounts create college-deployer --display-name="College GitHub deployer"

API_SA=college-api@$PROJECT_ID.iam.gserviceaccount.com
SCHED_SA=college-scheduler@$PROJECT_ID.iam.gserviceaccount.com
DEPLOY_SA=college-deployer@$PROJECT_ID.iam.gserviceaccount.com

# The running backend: database, secrets, Firebase Auth (verify tokens, manage admin/phone users), files
for role in roles/cloudsql.client roles/secretmanager.secretAccessor roles/firebaseauth.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$API_SA" --role="$role"
done
gcloud storage buckets add-iam-policy-binding "gs://$PROJECT_ID.firebasestorage.app" \
  --member="serviceAccount:$API_SA" --role=roles/storage.objectAdmin

# The deployer (GitHub Actions): push images, deploy Cloud Run services and jobs as the runtime account
for role in roles/run.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$DEPLOY_SA" --role="$role"
done
gcloud iam service-accounts add-iam-policy-binding "$API_SA" \
  --member="serviceAccount:$DEPLOY_SA" --role=roles/iam.serviceAccountUser
```

Also **share the Google Sheet** with `$API_SA` ([Google Sheets setup](05-google-sheets-setup.md)).

## 7. Keyless login for GitHub Actions (Workload Identity Federation)

GitHub proves its identity to Google with a short-lived token, so no key file is ever stored in GitHub.

```bash
gcloud iam workload-identity-pools create github --location=global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc github-provider --workload-identity-pool=github --location=global \
  --display-name="GitHub" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository=='$GITHUB_REPO'"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$GITHUB_REPO"
echo "GCP_WORKLOAD_IDENTITY_PROVIDER=projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github-provider"
echo "GCP_DEPLOY_SERVICE_ACCOUNT=$DEPLOY_SA"
```

Keep the two printed values for [Deployment, step 2](07-deployment.md#2-connect-github-actions-once).

## 8. Fill in the config files

In `config/production.env.yaml` (and `staging`):

| Placeholder | Value |
|---|---|
| `CORS_ALLOWED_ORIGINS` | `https://college.com,https://www.college.com` (your real domain) |
| `SHEETS_SPREADSHEET_ID` | ID from [Google Sheets setup](05-google-sheets-setup.md) |
| `INTERNAL_OIDC_AUDIENCE` | `https://college-api-$PROJECT_NUMBER.$REGION.run.app`. Run `echo https://college-api-$PROJECT_NUMBER.$REGION.run.app` to print it |

Also check `GCP_PROJECT_ID`, `CLOUD_SQL_CONNECTION_NAME` and `STORAGE_BUCKET`, and the values in `config/production.deploy.env`. They are pre-filled for project IDs `college-prod` and `college-staging`. If your project IDs differ, replace them everywhere in both files.

Now do the **first deployment** ([Deployment](07-deployment.md)). Then come back for step 9.

## 9. Scheduler job (after the first deployment)

This retries Google Sheets rows that couldn't be written immediately. Without it, those rows wait until someone presses "retry now" in the admin portal.

```bash
# Must be exactly the INTERNAL_OIDC_AUDIENCE value from config/<env>.env.yaml
SERVICE_URL=https://college-api-$PROJECT_NUMBER.$REGION.run.app
curl -s "$SERVICE_URL/api/v1/healthz"  # should print {"status":"ok",...}
gcloud iam service-accounts add-iam-policy-binding "$SCHED_SA" \
  --member="user:$(gcloud config get-value account)" --role=roles/iam.serviceAccountUser
gcloud scheduler jobs create http college-lead-sync --location="$REGION" --schedule="*/5 * * * *" \
  --uri="$SERVICE_URL/internal/lead-sync/flush" --http-method=POST \
  --oidc-service-account-email="$SCHED_SA" --oidc-token-audience="$SERVICE_URL" --attempt-deadline=120s
gcloud scheduler jobs run college-lead-sync --location="$REGION"  # test it now
```

Cloud Run services answer on two addresses (`...-<project-number>.<region>.run.app` and an older `...a.run.app` form). Both work; the audience only has to match `INTERNAL_OIDC_AUDIENCE` exactly. To check the result, open Cloud Console → Cloud Scheduler → `college-lead-sync`; the last run should say "Success".

## 10. Finally

Create the admin account ([Firebase setup → Creating the admin account](04-firebase-setup.md#creating-the-admin-account)) and set up monitoring alerts ([Operations → Monitoring and alerts](08-operations.md#monitoring-and-alerts)).
