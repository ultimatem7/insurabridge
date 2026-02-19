# Insurabridge Marketing Website

Public-facing marketing site for the Insurabridge healthcare claims automation platform.

## Overview

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **Purpose**: Drive trust, explain product, convert visitors to demo requests

## Site Structure

```
/                    - Home page with hero, features, CTA
/how-it-works        - Detailed process explanation
/security            - HIPAA compliance and security features
/demo                - Product screenshots and capabilities
/contact             - Demo request form
/privacy             - Privacy policy
/terms               - Terms of service
```

## Domain Setup

### Local Development (Current)

All URLs point to localhost:
- Marketing site: `http://localhost:3002`
- Product app: `http://localhost:3000`
- Backend API: `http://localhost:8000`

### Production (Future)

When ready to deploy:
- Marketing site: `https://insura.bridge`
- Product app: `https://app.insura.bridge`

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration.

### 3. Run Development Server

```bash
npm run dev
```

Visit http://localhost:3002

### 4. Build for Production

```bash
npm run build
npm start
```

## Features

### ✅ Pages Implemented
- Home page with hero section
- How It Works with detailed process flow
- Security & Compliance page
- Demo page with screenshots (placeholders)
- Contact page with working demo request form
- Privacy Policy
- Terms of Service

### ✅ Components
- Responsive header with navigation
- Footer with links and company info
- CTA (Call-to-Action) sections
- Demo request form with validation

### ✅ Features
- Responsive design (mobile, tablet, desktop)
- Tailwind CSS with custom healthcare theme
- Form validation with react-hook-form
- SEO optimization with metadata
- Accessibility features
- Clean, clinical design aesthetic

## Design System

### Colors

**Primary (Blue)**
- Used for CTAs, links, highlights
- Conveys trust and professionalism

**Clinical (Neutral Gray)**
- Main text and backgrounds
- Professional, clean aesthetic

**Success (Green)**
- Positive indicators, checkmarks
- Compliance badges

### Typography

- **Font**: Inter (system UI fallback)
- **Headings**: Bold, large scale
- **Body**: 18-20px for readability
- **Monospace**: For code examples

### Components

Custom Tailwind classes defined in `globals.css`:
- `.btn-primary` - Primary CTA buttons
- `.btn-secondary` - Secondary actions
- `.card` - Content cards
- `.badge` - Status/feature badges
- `.heading-1/2/3` - Heading styles

## API Endpoints

### Demo Request Form

**Endpoint**: `POST /api/demo-request`

**Payload**:
```json
{
  "name": "Dr. Jane Smith",
  "organization": "Memorial Hospital",
  "email": "jane@hospital.com",
  "role": "billing_manager",
  "ehr_vendor": "epic",
  "message": "Optional message"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Demo request received",
  "request_id": "DEMO-1234567890"
}
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

Configure custom domain:
- Root domain: `insura.bridge`
- App subdomain: `app.insura.bridge` → point to product backend

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3002
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t insurabridge-marketing .
docker run -p 3002:3002 insurabridge-marketing
```

### Static Export

For hosting on CDN/S3:

```bash
npm run build
npm run export
```

Output in `/out` directory.

## Customization

### Update Content

Edit page files in `src/app/`:
- `page.tsx` - Home page
- `how-it-works/page.tsx` - Process explanation
- `security/page.tsx` - Compliance info
- `demo/page.tsx` - Product demo
- `contact/page.tsx` - Contact form
- `privacy/page.tsx` - Privacy policy
- `terms/page.tsx` - Terms of service

### Update Branding

1. **Colors**: Edit `tailwind.config.ts`
2. **Logo**: Update in `src/components/Header.tsx`
3. **Favicon**: Add to `public/favicon.ico`
4. **Metadata**: Update in `src/app/layout.tsx`

### Add Screenshots

Replace placeholder divs in `src/app/demo/page.tsx` with:

```tsx
<img 
  src="/screenshots/dashboard.png" 
  alt="Product screenshot"
  className="rounded-lg shadow-lg"
/>
```

## SEO Optimization

### Implemented
- ✅ Meta tags for all pages
- ✅ OpenGraph tags
- ✅ Semantic HTML
- ✅ Descriptive page titles
- ✅ Alt text ready for images

### To Add
- Sitemap.xml (`src/app/sitemap.ts`)
- Robots.txt (`src/app/robots.ts`)
- Schema.org structured data
- Google Analytics / GTM

## Accessibility

- ✅ Semantic HTML elements
- ✅ ARIA labels where needed
- ✅ Keyboard navigation support
- ✅ Focus states on interactive elements
- ✅ Color contrast WCAG AA compliant
- ✅ Form validation with error messages

## Performance

- Server-side rendering for initial load
- Static page generation where possible
- Optimized images (use Next.js Image component)
- Minimal JavaScript bundle
- Tailwind CSS purging unused styles

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development

### File Structure

```
marketing-site/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   ├── how-it-works/       # How It Works page
│   │   ├── security/           # Security page
│   │   ├── demo/               # Demo page
│   │   ├── contact/            # Contact page
│   │   ├── privacy/            # Privacy page
│   │   ├── terms/              # Terms page
│   │   └── api/
│   │       └── demo-request/   # Demo form API
│   ├── components/
│   │   ├── Header.tsx          # Site header
│   │   ├── Footer.tsx          # Site footer
│   │   └── CTASection.tsx      # Reusable CTA
│   └── lib/                    # Utilities (if needed)
├── public/                     # Static assets
├── tailwind.config.ts          # Tailwind configuration
├── next.config.js              # Next.js configuration
└── package.json                # Dependencies
```

### Available Scripts

```bash
npm run dev      # Development server (port 3002)
npm run build    # Production build
npm run start    # Production server
npm run lint     # Run ESLint
```

## Production Checklist

Before deploying:

- [ ] Add real product screenshots to `/demo`
- [ ] Configure analytics (GA/GTM)
- [ ] Set up custom domain DNS
- [ ] Add favicon and app icons
- [ ] Test demo form submission
- [ ] Review all content for accuracy
- [ ] Add sitemap and robots.txt
- [ ] Test on mobile devices
- [ ] Run Lighthouse audit
- [ ] Configure CDN/caching

## Support

For questions about the marketing site:
- Review this README
- Check Next.js documentation
- Test locally with `npm run dev`

## License

Proprietary - All Rights Reserved

---

**Built for healthcare providers who deserve better tools. 🏥**
