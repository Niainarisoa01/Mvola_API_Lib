# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.4.x   | ✅ Yes             |
| < 1.4   | ❌ No              |

## Reporting a Vulnerability

If you discover a security vulnerability in this library, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email: **niainarisoa.mail@gmail.com**
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge your report within **48 hours** and provide a fix within **7 days** for critical vulnerabilities.

## Security Best Practices for Users

When using this library:

- **Never hardcode credentials** — Use environment variables or `.env` files
- **Keep `.env` files out of version control** — Ensure `.gitignore` includes `.env`
- **Use HTTPS callback URLs** — Never use HTTP for production callbacks
- **Rotate API keys regularly** — Regenerate consumer keys/secrets periodically
- **Monitor transaction logs** — Watch for unauthorized transaction patterns
- **Use sandbox for testing** — Never test with production credentials
