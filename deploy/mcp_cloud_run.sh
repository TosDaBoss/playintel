#!/usr/bin/env bash
# Deploy the PlayIntel MCP server to Cloud Run (pattern from Grove's deploy/cloud_run.sh).
#
# Run from the repository root after `gcloud auth login`:
#   source ~/.playintel_env            # sets PLAYINTEL_DATABASE_URL (the playintel_reader URL)
#   PROJECT_ID=... AUTHKIT_DOMAIN=https://<name>.authkit.app WORKOS_CLIENT_ID=client_... \
#     deploy/mcp_cloud_run.sh
#
# The reader URL goes into Secret Manager, never into the image, the repo or env flags.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID to the Google Cloud project}"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
REGION="${REGION:-europe-west2}"
SERVICE="${SERVICE:-playintel-mcp}"
RUNTIME_SA="${SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com"
SECRET="${SECRET:-playintel-reader-url}"
AUTHKIT="${AUTHKIT_DOMAIN:?set AUTHKIT_DOMAIN, e.g. https://<name>.authkit.app}"
# WorkOS puts the environment's client ID in the access token's aud claim
WORKOS_CLIENT_ID="${WORKOS_CLIENT_ID:?set WORKOS_CLIENT_ID (client_...)}"

# Cloud Run URLs are deterministic: https://SERVICE-PROJECT_NUMBER.REGION.run.app
HOST="${SERVICE}-${PROJECT_NUMBER}.${REGION}.run.app"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com --project "$PROJECT_ID"

# A dedicated runtime account that can read the one secret and nothing else
if ! gcloud iam service-accounts describe "$RUNTIME_SA" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SERVICE" --project "$PROJECT_ID" --display-name "PlayIntel MCP runtime"
fi

if ! gcloud secrets describe "$SECRET" --project "$PROJECT_ID" >/dev/null 2>&1; then
  : "${PLAYINTEL_DATABASE_URL:?source ~/.playintel_env first so the reader URL can be stored}"
  printf '%s' "$PLAYINTEL_DATABASE_URL" | gcloud secrets create "$SECRET" --project "$PROJECT_ID" \
    --replication-policy automatic --data-file=-
fi
gcloud secrets add-iam-policy-binding "$SECRET" --project "$PROJECT_ID" \
  --member "serviceAccount:${RUNTIME_SA}" --role roles/secretmanager.secretAccessor >/dev/null

# New projects do not let the default build account read the uploaded source (Grove pitfall)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role roles/run.builder --condition None --quiet >/dev/null

ENV_FILE="$(mktemp)"
trap 'rm -f "$ENV_FILE"' EXIT
cat > "$ENV_FILE" <<EOF
MCP_TRANSPORT: "http"
MCP_PUBLIC_URL: "https://${HOST}/mcp"
MCP_ALLOWED_HOSTS: "${HOST}"
OAUTH_ISSUER_URL: "${AUTHKIT}"
OAUTH_JWKS_URL: "${AUTHKIT}/oauth2/jwks"
OAUTH_AUDIENCE: "${WORKOS_CLIENT_ID}"
EOF

# --no-invoker-iam-check turns off Cloud Run's own Google sign-in gate so Claude and
# ChatGPT can reach the server; the server itself refuses every /mcp request without a
# valid WorkOS token. Grove uses it instead of --allow-unauthenticated because some
# organisations block granting roles to allUsers.
gcloud run deploy "$SERVICE" --source backend --project "$PROJECT_ID" --region "$REGION" \
  --service-account "$RUNTIME_SA" --env-vars-file "$ENV_FILE" \
  --set-secrets "DATABASE_URL=${SECRET}:latest" \
  --no-invoker-iam-check --min-instances 0 --max-instances 3 --memory 512Mi

# A rollback pins traffic to one revision; always move it to the one just deployed
gcloud run services update-traffic "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --to-latest

echo
echo "Share this page: https://${HOST}/"
echo "Connector URL:   https://${HOST}/mcp"
echo "Checks:"
echo "  curl -s https://${HOST}/health                                      # {\"status\":\"ok\"}"
echo "  curl -s -o /dev/null -w '%{http_code}\n' -X POST https://${HOST}/mcp   # 401"
echo "Logs: gcloud run services logs read $SERVICE --project $PROJECT_ID --region $REGION --limit 40"
