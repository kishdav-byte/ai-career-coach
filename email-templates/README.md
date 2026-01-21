# Supabase Email Templates - Total Package Interview

These are branded email templates for Supabase authentication emails that match the Total Package Interview brand identity.

## 🎨 Brand Colors Used
- **Primary Navy**: `#0f172a`, `#1e293b`
- **Accent Teal**: `#20C997`, `#34d399`
- **Text Colors**: `#ffffff` (white), `#94a3b8` (muted), `#64748b` (subtle)

## 📧 Templates Included

1. **confirm-signup.html** - Email confirmation for new signups
2. **reset-password.html** - Password reset email
3. **magic-link.html** - Passwordless login magic link
4. **change-email.html** - Email address change confirmation

## 🚀 How to Install These Templates

### Step 1: Access Supabase Dashboard
1. Go to https://app.supabase.com/project/nvfjmqacxzlmfamiynuu
2. Navigate to **Authentication** → **Email Templates**

### Step 2: Update Each Template

For each template type (Confirm signup, Magic Link, Reset Password, Change Email):

1. Click on the template you want to edit
2. Switch to **HTML** mode (not plain text)
3. Copy the entire content from the corresponding `.html` file
4. Paste it into the Supabase template editor
5. Click **Save**

### Step 3: Configure Email Settings (Optional)

In **Authentication** → **Settings** → **Email**:
- Set your **Site URL** (e.g., `https://yourdomain.com`)
- Configure **Redirect URLs** if needed
- Customize the **From** email address (requires custom SMTP)

## 📝 Template Variables

These Supabase variables are automatically replaced in the emails:

- `{{ .ConfirmationURL }}` - The confirmation/action link
- `{{ .Token }}` - The confirmation token
- `{{ .TokenHash }}` - Hashed token
- `{{ .SiteURL }}` - Your site URL (configured in Supabase)
- `{{ .Email }}` - User's email address

## 🎯 Features

✅ **Fully Responsive** - Works on all email clients and devices  
✅ **Brand Aligned** - Matches your Total Package Interview design  
✅ **Professional** - Modern glassmorphism and gradient design  
✅ **Accessible** - High contrast, readable fonts  
✅ **Email Client Compatible** - Tested for Gmail, Outlook, Apple Mail, etc.

## 🔧 Customization

To customize these templates further:

1. **Update the Site URL**: Replace `{{ .SiteURL }}` references with your actual domain
2. **Add Social Links**: Add footer links to your social media
3. **Change Colors**: Update the hex color codes to match any brand changes
4. **Add Logo**: If you have a logo image, host it and add an `<img>` tag in the header

## 📱 Testing

Before deploying:
1. Send test emails from Supabase dashboard
2. Check how they look on different email clients
3. Test all links work correctly
4. Verify mobile responsiveness

## 🆘 Support

If you need help:
- Supabase Docs: https://supabase.com/docs/guides/auth/auth-email-templates
- Email Testing Tool: https://www.emailonacid.com/

---

**Created for Total Package Interview**  
Last Updated: January 2026
