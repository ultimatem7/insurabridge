# Marketing Site Deployment Guide

## Overview

This is the public-facing marketing website for Insurabridge. It should be deployed at the **root domain** while the product app runs on a subdomain.

**Domains:**
- Marketing: `https://insura.bridge`
- Product: `https://app.insura.bridge`

---

## Quick Start (Development)

```bash
cd marketing-site

# Install dependencies
npm install

# Run development server
npm run dev
```

Visit: http://localhost:3002

---

## Production Deployment Options

### Option 1: Vercel (Recommended for Static Sites)

**Step 1: Install Vercel CLI**
```bash
npm i -g vercel
```

**Step 2: Deploy**
```bash
cd marketing-site
vercel
```

**Step 3: Configure Custom Domain**

In Vercel dashboard:
1. Go to your project settings
2. Add domain: `insura.bridge`
3. Configure DNS records as instructed

**Step 4: Configure Product Subdomain**

Point `app.insura.bridge` to your product backend:
- Create CNAME record: `app` → your product server
- Or add in Vercel proxy rules

### Option 2: Docker + Nginx

**Step 1: Build Docker Image**

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3002
CMD ["node", "server.js"]
```

**Step 2: Build and Run**
```bash
docker build -t insurabridge-marketing .
docker run -p 3002:3002 insurabridge-marketing
```

**Step 3: Nginx Reverse Proxy**

```nginx
# /etc/nginx/sites-available/insurabridge

# Marketing site (root domain)
server {
    listen 443 ssl http2;
    server_name insura.bridge;
    
    ssl_certificate /etc/ssl/certs/insura.bridge.crt;
    ssl_certificate_key /etc/ssl/private/insura.bridge.key;
    
    location / {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Product app (subdomain)
server {
    listen 443 ssl http2;
    server_name app.insura.bridge;
    
    ssl_certificate /etc/ssl/certs/insura.bridge.crt;
    ssl_certificate_key /etc/ssl/private/insura.bridge.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name insura.bridge app.insura.bridge;
    return 301 https://$server_name$request_uri;
}
```

### Option 3: Static Export to CDN

**Step 1: Build Static Site**

Update `next.config.js`:
```javascript
module.exports = {
  output: 'export',
  images: {
    unoptimized: true, // Required for static export
  },
}
```

**Step 2: Export**
```bash
npm run build
```

Static files will be in the `/out` directory.

**Step 3: Upload to CDN**

Upload to:
- AWS S3 + CloudFront
- Netlify
- Cloudflare Pages
- Azure Static Web Apps

---

## DNS Configuration

### Root Domain (Marketing)

**A Record:**
```
insura.bridge    →    your-server-ip
```

**Or CNAME (if using Vercel/Netlify):**
```
insura.bridge    →    cname.vercel-dns.com
```

### Product Subdomain

**A Record:**
```
app.insura.bridge    →    your-product-server-ip
```

**Or CNAME:**
```
app.insura.bridge    →    your-product-server.com
```

---

## SSL/TLS Certificates

### Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d insura.bridge -d app.insura.bridge

# Auto-renewal
sudo certbot renew --dry-run
```

### Commercial Certificate

Upload to:
- Nginx: `/etc/ssl/certs/` and `/etc/ssl/private/`
- Cloudflare: Dashboard → SSL/TLS → Origin Certificates
- Vercel: Automatic with custom domains

---

## Environment Variables

### Production

Create `.env.production`:

```env
NEXT_PUBLIC_SITE_URL=https://insura.bridge
NEXT_PUBLIC_APP_URL=https://app.insura.bridge
NEXT_PUBLIC_API_URL=https://app.insura.bridge/api
NEXT_PUBLIC_CONTACT_EMAIL=demo@insura.bridge
```

### Development

Already configured in `.env.local`

---

## Demo Form Integration

### Current Implementation

The form posts to `/api/demo-request` (Next.js API route).

**For production**, integrate with:

1. **Email Service**
   ```typescript
   // Install: npm install nodemailer
   import nodemailer from 'nodemailer'
   
   const transporter = nodemailer.createTransport({
     host: process.env.SMTP_HOST,
     port: 587,
     auth: {
       user: process.env.SMTP_USER,
       pass: process.env.SMTP_PASS,
     }
   })
   ```

2. **CRM Integration**
   - Salesforce API
   - HubSpot Forms API
   - Mailchimp
   - SendGrid

3. **Database Storage**
   - Save to PostgreSQL
   - MongoDB
   - Firebase

---

## Performance Optimization

### Implemented
- Static page generation
- Tailwind CSS purging
- Component code splitting

### To Add
- Next.js Image optimization
- Font optimization
- Lazy loading for images
- Caching headers

---

## SEO Optimization

### Current
- ✅ Meta tags on all pages
- ✅ OpenGraph tags
- ✅ Semantic HTML
- ✅ Descriptive titles

### To Add

**Sitemap** (`src/app/sitemap.ts`):
```typescript
export default function sitemap() {
  return [
    { url: 'https://insura.bridge', lastModified: new Date() },
    { url: 'https://insura.bridge/how-it-works', lastModified: new Date() },
    { url: 'https://insura.bridge/security', lastModified: new Date() },
    { url: 'https://insura.bridge/demo', lastModified: new Date() },
    { url: 'https://insura.bridge/contact', lastModified: new Date() },
  ]
}
```

**Robots.txt** (`src/app/robots.ts`):
```typescript
export default function robots() {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    sitemap: 'https://insura.bridge/sitemap.xml',
  }
}
```

---

## Analytics

### Google Analytics 4

**Step 1: Install**
```bash
npm install @next/third-parties
```

**Step 2: Add to Layout**
```typescript
import { GoogleAnalytics } from '@next/third-parties/google'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <GoogleAnalytics gaId="G-XXXXXXXXXX" />
      </body>
    </html>
  )
}
```

---

## Monitoring

### Health Check Endpoint

Already available at:
- Development: http://localhost:3002/
- Production: https://insura.bridge/

### Uptime Monitoring

Use services like:
- UptimeRobot
- Pingdom
- StatusCake

---

## Security Headers

Add to `next.config.js`:

```javascript
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ]
  },
}
```

---

## Testing Checklist

Before going live:

- [ ] All pages load correctly
- [ ] Demo form submits successfully
- [ ] Mobile responsive design works
- [ ] Links to `app.insura.bridge` work
- [ ] SSL certificate valid
- [ ] DNS records configured
- [ ] Analytics tracking works
- [ ] Form validation works
- [ ] Images load properly
- [ ] Page load speed < 3s
- [ ] Accessibility audit passes
- [ ] SEO meta tags correct

---

## Troubleshooting

### Build Fails

```bash
# Clear cache
rm -rf .next
npm run build
```

### Port Already in Use

```bash
# Use different port
npm run dev -- -p 3003
```

### Form Not Submitting

Check browser console and Network tab. Verify `/api/demo-request` endpoint is working.

---

## Support

For deployment issues:
- Review Next.js documentation: https://nextjs.org/docs
- Check this guide
- Test locally first

---

**Ready to deploy!** 🚀
