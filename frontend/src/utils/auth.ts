import usersData from '../data/users.json';

export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  company: string;
  role: 'user' | 'admin' | 'super-admin';
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  company: string;
}

class AuthService {
  private users: User[] = (usersData.users as User[]);

  constructor() {
    // Load users from localStorage if available
    const storedUsers = localStorage.getItem('users');
    if (storedUsers) {
      this.users = JSON.parse(storedUsers);
    } else {
      // Initialize with default users
      localStorage.setItem('users', JSON.stringify(this.users));
    }
  }

  private saveUsers(): void {
    localStorage.setItem('users', JSON.stringify(this.users));
  }

  login(credentials: LoginCredentials): User | null {
    const user = this.users.find(
      u => u.email === credentials.email && u.password === credentials.password
    );
    
    if (user) {
      // Store current user in session
      const { password, ...userWithoutPassword } = user;
      localStorage.setItem('currentUser', JSON.stringify(userWithoutPassword));
      return user;
    }
    
    return null;
  }

  register(userData: RegisterData): User | null {
    // Check if user already exists
    if (this.users.find(u => u.email === userData.email)) {
      return null;
    }

    const newUser: User = {
      id: Date.now().toString(),
      ...userData,
      role: 'user', // Default role
      createdAt: new Date().toISOString()
    };

    this.users.push(newUser);
    this.saveUsers();

    // Auto-login after registration
    const { password, ...userWithoutPassword } = newUser;
    localStorage.setItem('currentUser', JSON.stringify(userWithoutPassword));

    return newUser;
  }

  logout(): void {
    localStorage.removeItem('currentUser');
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('currentUser');
    if (userStr) {
      const user = JSON.parse(userStr);
      // Get full user data including password
      return this.users.find(u => u.id === user.id) || null;
    }
    return null;
  }

  isAuthenticated(): boolean {
    return this.getCurrentUser() !== null;
  }

  hasRole(role: 'user' | 'admin' | 'super-admin'): boolean {
    const user = this.getCurrentUser();
    if (!user) return false;

    const roleHierarchy = {
      'user': 1,
      'admin': 2,
      'super-admin': 3
    };

    return roleHierarchy[user.role] >= roleHierarchy[role];
  }

  getAllUsers(): User[] {
    return this.users.map(user => {
      const { password, ...userWithoutPassword } = user;
      return userWithoutPassword as User;
    });
  }

  createAdmin(userData: RegisterData): User | null {
    if (!this.hasRole('super-admin')) {
      return null;
    }

    if (this.users.find(u => u.email === userData.email)) {
      return null;
    }

    const newAdmin: User = {
      id: Date.now().toString(),
      ...userData,
      role: 'admin',
      createdAt: new Date().toISOString()
    };

    this.users.push(newAdmin);
    this.saveUsers();
    return newAdmin;
  }

  deleteUser(userId: string): boolean {
    if (!this.hasRole('super-admin')) {
      return false;
    }

    const userIndex = this.users.findIndex(u => u.id === userId);
    if (userIndex === -1) return false;

    // Don't allow super-admin to delete themselves
    const currentUser = this.getCurrentUser();
    if (currentUser && currentUser.id === userId) {
      return false;
    }

    this.users.splice(userIndex, 1);
    this.saveUsers();
    return true;
  }

  updateUserRole(userId: string, newRole: 'user' | 'admin'): boolean {
    if (!this.hasRole('super-admin')) {
      return false;
    }

    const user = this.users.find(u => u.id === userId);
    if (!user) return false;

    // Don't allow changing super-admin role
    if (user.role === 'super-admin') {
      return false;
    }

    user.role = newRole;
    this.saveUsers();
    return true;
  }
}

export const authService = new AuthService(); 