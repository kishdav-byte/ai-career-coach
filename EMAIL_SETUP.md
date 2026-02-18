# Email & Notification Setup Guide (Namecheap Edition)

## ✅ Using Namecheap Private Email
You can absolutely use your Namecheap emails! This is often easier since you already own them.

---

## Part 1: Gather Credentials
You need the password for the email account you want to send from (e.g., `noreply@totalpackageinterview.com`).
*   **Host**: `mail.privateemail.com`
*   **Port**: `465` (Secure SSL)
*   **User**: `noreply@totalpackageinterview.com`
*   **Password**: [The password you use to log in to this email]

---

## Part 2: Configure Supabase (For Auth Emails)
This fixes the "Bounce" alert and handles Signups/Password Resets.

1. Log in to your **Supabase Dashboard**.
2. Go to **Project Settings** -> **Authentication** -> **SMTP Settings**.
3. Toggle **Enable Custom SMTP**.
4. Enter the Namecheap details:
   - **Sender Email**: `noreply@totalpackageinterview.com`
   - **Sender Name**: Total Package Interview
   - **Host**: `mail.privateemail.com`
   - **Port**: `465`
   - **User**: `noreply@totalpackageinterview.com`
   - **Password**: [Your Email Password]
   - **Encryption**: `SSL` (Since we are using port 465)
5. Click **Save**.

---

## Part 3: Configure Local Environment (For SMS Notifications)
This enables the new "New User SMS" feature (`864...`) to work using your Namecheap account.

1. Open your local `.env` file.
2. Update the SMTP variables to match Namecheap:

```bash
# Email Provider Settings (Namecheap)
SMTP_HOST=mail.privateemail.com
SMTP_PORT=465
SMTP_USER=noreply@totalpackageinterview.com
SMTP_PASS=[PASTE YOUR EMAIL PASSWORD HERE]
SMTP_SENDER=noreply@totalpackageinterview.com
```

3. **Restart your local python server**:
   - Click in the terminal
   - Press `CTRL+C` to stop
   - Run `python3 run_local.py` to restart
