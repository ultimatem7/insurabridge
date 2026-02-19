'use client'

import Link from 'next/link'
import { User, Settings, LogOut } from 'lucide-react'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="text-xl font-bold text-foreground">
              Insurabridge
            </span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center space-x-6">
            <Link
              href="/pipeline"
              className="text-sm font-medium text-foreground-secondary hover:text-foreground transition-colors"
            >
              Pipeline
            </Link>
            <Link
              href="/claims"
              className="text-sm font-medium text-foreground-secondary hover:text-foreground transition-colors"
            >
              Claims
            </Link>
            
            {/* User Menu */}
            <div className="flex items-center space-x-4 ml-4 pl-4 border-l border-border">
              <button className="p-2 text-foreground-secondary hover:text-foreground hover:bg-background-tertiary rounded-lg transition-colors">
                <Settings className="w-5 h-5" />
              </button>
              <button className="p-2 text-foreground-secondary hover:text-foreground hover:bg-background-tertiary rounded-lg transition-colors">
                <User className="w-5 h-5" />
              </button>
              <a
                href="http://localhost:3002"
                className="p-2 text-foreground-secondary hover:text-danger hover:bg-background-tertiary rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
