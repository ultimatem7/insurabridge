/**
 * Initialize database with demo user
 * Run this script once to set up the database
 */

import { createUser } from './auth'
import db from './db'

async function initializeDatabase() {
  console.log('Initializing database...')
  
  // Create demo user
  try {
    await createUser('demo@insura.bridge', 'demo1234', 'Demo User')
    console.log('✓ Demo user created: demo@insura.bridge / demo1234')
  } catch (error: any) {
    if (error.message === 'User already exists') {
      console.log('✓ Demo user already exists')
    } else {
      console.error('Error creating demo user:', error)
    }
  }
  
  // Get user count
  const userCount = db.getUserCount()
  console.log(`✓ Total users in database: ${userCount}`)
  
  console.log('\nDatabase initialized successfully!')
  console.log('\nYou can now log in with:')
  console.log('  Email: demo@insura.bridge')
  console.log('  Password: demo1234')
  console.log('\nDatabase location: data/users.json')
}

initializeDatabase()
