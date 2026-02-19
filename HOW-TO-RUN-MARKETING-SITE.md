# How to Run the Insurabridge Marketing Site

## Location

```
/Users/mingchuan/Desktop/insurabridge/marketing-site/
```

---

## Quick Start (2 Commands)

```bash
# Navigate to the marketing site
cd /Users/mingchuan/Desktop/insurabridge/marketing-site

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Access at:** http://localhost:3002

---

## Available Commands

### Development Mode

```bash
npm run dev
```

Starts the development server with hot reload.
- URL: http://localhost:3002
- Changes auto-refresh
- Full error reporting

### Production Build

```bash
npm run build
```

Creates an optimized production build.
- Validates all code
- Generates static pages
- Optimizes assets

### Production Server

```bash
npm run build
npm start
```

Runs the production-optimized server.
- Must build first
- Runs on port 3002
- Production performance

### Check for Issues

```bash
npm run lint
```

Runs ESLint to check for code issues.

---

## What You'll See

### Home Page (/)
- Hero section with "Automated Insurance Claims from EHR Data"
- How It Works (4-step overview)
- Security & Compliance highlights
- Who It's For section
- Call-to-action buttons

### Navigation Links
- How It Works → Detailed process explanation
- Security → HIPAA compliance and security features
- Demo → Product screenshots and capabilities
- Contact → Demo request form
- Privacy → Privacy policy
- Terms → Terms of service

### Interactive Features
- Responsive mobile menu
- Working contact form
- Form validation
- Success messages

---

## Testing the Demo Form

1. Go to http://localhost:3002/contact
2. Fill out all required fields:
   - Name
   - Organization
   - Email (must be valid format)
   - Role (select from dropdown)
   - EHR Vendor (select from dropdown)
   - Message (optional)
3. Click "Request Demo"
4. See success message
5. Check browser console for submitted data

---

## Project Structure

```
marketing-site/
├── src/app/              # All pages
│   ├── page.tsx         # Home
│   ├── how-it-works/    # Process page
│   ├── security/        # Security page
│   ├── demo/            # Demo page
│   ├── contact/         # Contact form
│   ├── privacy/         # Privacy policy
│   └── terms/           # Terms of service
├── src/components/      # Reusable components
└── public/              # Static files
```

---

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
npm run dev -- -p 3003
```

### Dependencies Missing

```bash
# Reinstall all dependencies
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

---

## Next Steps

1. ✅ Site is running locally
2. Review content on all pages
3. Test form submission
4. Add real product screenshots (optional)
5. Deploy to production when ready

---

## Documentation

- **README.md** - Full technical documentation
- **QUICKSTART.md** - Fast setup guide
- **DEPLOYMENT.md** - Production deployment
- **PROJECT-OVERVIEW.md** - Executive summary

---

## Need Help?

1. Check the README.md for detailed docs
2. Review QUICKSTART.md for basics
3. See DEPLOYMENT.md for production setup

---

**That's it! The marketing site should now be running at http://localhost:3002** 🚀
