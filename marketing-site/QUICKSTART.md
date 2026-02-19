# Quick Start Guide

Get the Insurabridge marketing site running in under 2 minutes.

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

## Steps

### 1. Install Dependencies

```bash
cd marketing-site
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The site will be available at: **http://localhost:3002**

### 3. Build for Production

```bash
npm run build
npm start
```

## What's Included

✅ **7 Complete Pages**
- Home with hero section
- How It Works
- Security & Compliance
- Demo
- Contact (with working form)
- Privacy Policy
- Terms of Service

✅ **Features**
- Fully responsive design
- Tailwind CSS styling
- Form validation
- SEO optimized
- Accessible
- Healthcare-focused design

✅ **Components**
- Header with navigation
- Footer with links
- CTA sections
- Demo request form

## Testing the Demo Form

1. Go to http://localhost:3002/contact
2. Fill out the form
3. Submit
4. Check browser console for form data
5. You'll see a success message

The form data is logged to the console. In production, you'll integrate with your CRM or email service.

## Customization

### Update Content
Edit files in `src/app/`:
- `page.tsx` - Home page
- `how-it-works/page.tsx` - Process explanation
- `security/page.tsx` - Security info
- `demo/page.tsx` - Product demo
- `contact/page.tsx` - Contact form

### Update Styling
Edit `tailwind.config.ts` for colors and theme.

### Add Product Screenshots
Replace placeholder divs in `src/app/demo/page.tsx` with:

```tsx
<img 
  src="/screenshots/dashboard.png" 
  alt="Dashboard"
  className="rounded-lg shadow-lg w-full"
/>
```

Add images to `public/screenshots/`

## Next Steps

1. ✅ Site is built and tested
2. Add real product screenshots
3. Configure environment variables
4. Deploy to production
5. Point DNS to deployment

See `DEPLOYMENT.md` for detailed deployment instructions.

## Need Help?

- Check `README.md` for full documentation
- Review Next.js docs: https://nextjs.org/docs
- Test locally with `npm run dev`

---

**Built with Next.js 14, React, TypeScript, and Tailwind CSS** 🚀
