import bcrypt from 'bcryptjs'
import { SignJWT, jwtVerify } from 'jose'
import db from './db'

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'insurabridge-secret-key-change-in-production'
)

export interface User {
  id: number
  email: string
  name: string | null
}

// Hash password
export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10)
}

// Verify password
export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash)
}

// Create JWT token
export async function createToken(user: User): Promise<string> {
  const token = await new SignJWT({ 
    userId: user.id,
    email: user.email,
    name: user.name
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(JWT_SECRET)
  
  return token
}

// Verify JWT token
export async function verifyToken(token: string): Promise<User | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET)
    return {
      id: payload.userId as number,
      email: payload.email as string,
      name: payload.name as string | null,
    }
  } catch (error) {
    return null
  }
}

// Create user
export async function createUser(email: string, password: string, name?: string): Promise<User> {
  const hashedPassword = await hashPassword(password)
  
  try {
    const user = db.createUser(email, hashedPassword, name || null)
    
    return {
      id: user.id,
      email: user.email,
      name: user.name,
    }
  } catch (error: any) {
    if (error.message === 'User already exists') {
      throw error
    }
    throw new Error('Failed to create user')
  }
}

// Find user by email
export function findUserByEmail(email: string): any {
  return db.findUserByEmail(email)
}

// Update last login
export function updateLastLogin(userId: number): void {
  db.updateLastLogin(userId)
}

// Authenticate user
export async function authenticateUser(email: string, password: string): Promise<User | null> {
  const user = findUserByEmail(email)
  
  if (!user) {
    return null
  }
  
  const isValid = await verifyPassword(password, user.password)
  
  if (!isValid) {
    return null
  }
  
  // Update last login
  updateLastLogin(user.id)
  
  return {
    id: user.id,
    email: user.email,
    name: user.name,
  }
}
