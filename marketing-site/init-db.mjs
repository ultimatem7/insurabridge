import fs from 'fs'
import path from 'path'
import bcrypt from 'bcryptjs'

// Create data directory
const dataDir = path.join(process.cwd(), 'data')
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true })
}

// Create database file
const dbPath = path.join(dataDir, 'users.json')

// Hash demo password
const hashedPassword = await bcrypt.hash('demo1234', 10)

// Create initial database
const initialDb = {
  users: [
    {
      id: 1,
      email: 'demo@insura.bridge',
      password: hashedPassword,
      name: 'Demo User',
      created_at: new Date().toISOString(),
      last_login: null,
    }
  ],
  nextId: 2,
}

// Write database
fs.writeFileSync(dbPath, JSON.stringify(initialDb, null, 2))

console.log('✓ Database initialized successfully!')
console.log('✓ Demo user created: demo@insura.bridge / demo1234')
console.log(`✓ Database location: ${dbPath}`)
console.log('\nYou can now log in with:')
console.log('  Email: demo@insura.bridge')
console.log('  Password: demo1234')
