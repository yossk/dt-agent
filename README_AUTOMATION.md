# Email Automation Service

## Overview

The Email Automation Service automatically watches an email mailbox (IMAP) for incoming quote emails and processes them automatically, eliminating the need for manual file handling.

## Features

- **Automatic Email Watching**: Continuously monitors IMAP mailbox for new emails
- **Smart Filtering**: Only processes emails matching configured criteria (domain, keywords, attachments)
- **Auto-Processing**: Automatically runs quote extraction and generation workflow
- **Email Organization**: Moves processed emails to a "Processed" folder
- **Duplicate Prevention**: Tracks processed emails to avoid reprocessing

## Setup

### 1. Configuration

Edit your `config.yaml` file and enable email automation:

```yaml
email_automation:
  enabled: true
  method: "imap"
  
  imap:
    server: "imap.gmail.com"  # Your IMAP server
    port: 993
    username: "quotes@company.com"
    password: "${EMAIL_PASSWORD}"  # Use environment variable
    folder: "INBOX"
    processed_folder: "Processed"
    check_interval_seconds: 30
  
  filters:
    from_domains:
      - "@vendor.com"
      - "@supplier.com"
    subject_keywords:
      - "quote"
      - "price"
    has_attachments: true
```

### 2. Set Environment Variable

Set your email password as an environment variable:

```bash
export EMAIL_PASSWORD="your-email-password"
```

For Gmail, you may need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### 3. Run the Service

```bash
# From project root
python -m src.automation --config config/config.yaml
```

Or as a module:

```bash
python -m src.automation --config local-testing/config/config.local.yaml
```

### 4. Run as a Service (Linux)

Create a systemd service file `/etc/systemd/system/dt-agent-automation.service`:

```ini
[Unit]
Description=DT-Agent Email Automation Service
After=network.target

[Service]
Type=simple
User=dt-agent
WorkingDirectory=/opt/dt-agent
Environment="EMAIL_PASSWORD=your-password"
ExecStart=/usr/bin/python3 -m src.automation --config /etc/dt-agent/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable dt-agent-automation
sudo systemctl start dt-agent-automation
sudo systemctl status dt-agent-automation
```

## How It Works

1. **Connection**: Connects to IMAP server using provided credentials
2. **Monitoring**: Checks mailbox every N seconds (configurable)
3. **Filtering**: Only fetches emails matching filter criteria
4. **Processing**: Runs each email through the quote processing workflow
5. **Organization**: Moves processed emails to "Processed" folder
6. **Logging**: Logs all activity for monitoring

## Email Filters

The service uses three types of filters:

### From Domain Filter
Only process emails from specific domains:
```yaml
filters:
  from_domains:
    - "@vendor.com"
    - "@supplier.com"
```

Empty list = accept from any domain.

### Subject Keywords Filter
Only process emails with specific keywords in subject:
```yaml
filters:
  subject_keywords:
    - "quote"
    - "price"
    - "quotation"
```

Empty list = accept any subject.

### Attachment Filter
Only process emails with attachments:
```yaml
filters:
  has_attachments: true
```

## Logs

The service logs to the same logging system as the main application. Check logs for:
- Connection status
- Emails found and processed
- Processing results (success/failure)
- Errors

View logs:
```bash
tail -f /data/logs/dt-agent.log
```

## Troubleshooting

### Connection Failed
- Verify IMAP server address and port
- Check username and password
- For Gmail: Enable "Less secure app access" or use App Password
- Check firewall settings

### No Emails Processed
- Check filter settings (may be too restrictive)
- Verify emails have attachments if `has_attachments: true`
- Check email subject matches keywords
- Look for "Skipping email" messages in logs

### Emails Not Moved to Processed Folder
- Check folder permissions
- Verify processed folder exists or can be created
- Some IMAP servers may not support folder operations

### Permission Denied
- Ensure email account has IMAP access enabled
- For Gmail, may need to enable IMAP in account settings

## Security Best Practices

1. **Use Environment Variables**: Never put passwords in config files
2. **App Passwords**: Use app-specific passwords for Gmail
3. **Restrictive Filters**: Use domain filters to only accept authorized senders
4. **Read-Only Access**: If possible, use read-only IMAP access
5. **Regular Monitoring**: Review logs regularly for suspicious activity

## Future Enhancements

- Microsoft Graph API support (for Office365/Exchange)
- Webhook support for real-time processing
- Email response automation
- Processing queue with retry logic
- Web dashboard for monitoring

