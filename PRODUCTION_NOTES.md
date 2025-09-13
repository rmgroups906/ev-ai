Production checklist:
- Set SECRET_KEYS env var (comma-separated) with at least one secure random key.
- Configure DATABASE_URL to Postgres in production.
- Configure SMTP_* for email and TWILIO_* for SMS.
- Configure S3 bucket and AWS credentials if using S3 to persist models.
- Use a secrets manager for SECRET_KEYS and DB credentials.
- Configure nginx with TLS (Let's Encrypt) and terminate TLS there; proxy to backend via http.
- Ensure Redis is secured and not exposed publicly.
- Add monitoring (Prometheus/Grafana) and logs aggregation (ELK/CloudWatch).