import fs from 'fs'
import path from 'path'

// Database file location
const dbDir = path.join(process.cwd(), 'data')
const dbPath = path.join(dbDir, 'users.json')

interface User {
  id: number
  email: string
  password: string
  name: string | null
  created_at: string
  last_login: string | null
}

interface Database {
  users: User[]
  nextId: number
}

// Ensure data directory exists
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true })
}

// Initialize database file if it doesn't exist
if (!fs.existsSync(dbPath)) {
  const initialDb: Database = {
    users: [],
    nextId: 1,
  }
  fs.writeFileSync(dbPath, JSON.stringify(initialDb, null, 2))
}

// Read database
function readDb(): Database {
  const data = fs.readFileSync(dbPath, 'utf-8')
  return JSON.parse(data)
}

// Write database
function writeDb(db: Database): void {
  fs.writeFileSync(dbPath, JSON.stringify(db, null, 2))
}

// Database operations
export const db = {
  // Find user by email
  findUserByEmail(email: string): User | undefined {
    const data = readDb()
    return data.users.find(u => u.email === email)
  },

  // Create user
  createUser(email: string, password: string, name: string | null): User {
    const data = readDb()
    
    // Check if user exists
    if (data.users.some(u => u.email === email)) {
      throw new Error('User already exists')
    }
    
    const user: User = {
      id: data.nextId,
      email,
      password,
      name,
      created_at: new Date().toISOString(),
      last_login: null,
    }
    
    data.users.push(user)
    data.nextId++
    writeDb(data)
    
    return user
  },

  // Update last login
  updateLastLogin(userId: number): void {
    const data = readDb()
    const user = data.users.find(u => u.id === userId)
    if (user) {
      user.last_login = new Date().toISOString()
      writeDb(data)
    }
  },

  // Get all users (for admin)
  getAllUsers(): User[] {
    const data = readDb()
    return data.users.map(u => ({
      ...u,
      password: '[REDACTED]' // Don't expose passwords
    })) as User[]
  },

  // Get user count
  getUserCount(): number {
    const data = readDb()
    return data.users.length
  },
}

export default db
