import { useState, useEffect } from 'react';
import { Shield, UserPlus, Trash2, Edit, Users, Crown } from 'lucide-react';
import { authService } from '../utils/auth';
import type { User, RegisterData } from '../utils/auth';

export default function AdminManagement() {
    const [users, setUsers] = useState<User[]>([]);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [formData, setFormData] = useState<RegisterData>({
        firstName: '',
        lastName: '',
        email: '',
        password: '',
        company: ''
    });
    const [errors, setErrors] = useState<{ [key: string]: string }>({});
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        loadUsers();
    }, []);

    const loadUsers = () => {
        const allUsers = authService.getAllUsers();
        setUsers(allUsers);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    const validateForm = () => {
        const newErrors: { [key: string]: string } = {};

        if (!formData.firstName.trim()) {
            newErrors.firstName = 'First name is required';
        }

        if (!formData.lastName.trim()) {
            newErrors.lastName = 'Last name is required';
        }

        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }

        if (!formData.company.trim()) {
            newErrors.company = 'Company name is required';
        }

        if (!editingUser && !formData.password) {
            newErrors.password = 'Password is required';
        } else if (!editingUser && formData.password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleCreateAdmin = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        setIsLoading(true);
        setMessage(null);

        try {
            const newAdmin = authService.createAdmin(formData);
            
            if (newAdmin) {
                setMessage({ type: 'success', text: 'Admin created successfully!' });
                setShowCreateForm(false);
                resetForm();
                loadUsers();
            } else {
                setMessage({ type: 'error', text: 'Failed to create admin. Email might already exist.' });
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'An error occurred while creating admin.' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteUser = (userId: string) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            const success = authService.deleteUser(userId);
            
            if (success) {
                setMessage({ type: 'success', text: 'User deleted successfully!' });
                loadUsers();
            } else {
                setMessage({ type: 'error', text: 'Failed to delete user.' });
            }
        }
    };

    const handleUpdateRole = (userId: string, newRole: 'user' | 'admin') => {
        const success = authService.updateUserRole(userId, newRole);
        
        if (success) {
            setMessage({ type: 'success', text: 'User role updated successfully!' });
            loadUsers();
        } else {
            setMessage({ type: 'error', text: 'Failed to update user role.' });
        }
    };

    const resetForm = () => {
        setFormData({
            firstName: '',
            lastName: '',
            email: '',
            password: '',
            company: ''
        });
        setErrors({});
        setEditingUser(null);
    };

    const getRoleBadge = (role: string) => {
        const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
        
        switch (role) {
            case 'super-admin':
                return (
                    <span className={`${baseClasses} bg-red-100 text-red-800 flex items-center gap-1`}>
                        <Crown className="w-3 h-3" />
                        Super Admin
                    </span>
                );
            case 'admin':
                return (
                    <span className={`${baseClasses} bg-blue-100 text-blue-800 flex items-center gap-1`}>
                        <Shield className="w-3 h-3" />
                        Admin
                    </span>
                );
            default:
                return (
                    <span className={`${baseClasses} bg-gray-100 text-gray-800 flex items-center gap-1`}>
                        <Users className="w-3 h-3" />
                        User
                    </span>
                );
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Admin Management</h1>
                                <p className="text-gray-600">Manage users and their roles</p>
                            </div>
                            <button
                                onClick={() => setShowCreateForm(true)}
                                className="bg-[#1e40af] text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                            >
                                <UserPlus className="w-4 h-4" />
                                Create Admin
                            </button>
                        </div>
                    </div>

                    {message && (
                        <div className={`px-6 py-3 ${
                            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                        }`}>
                            {message.text}
                        </div>
                    )}

                    {showCreateForm && (
                        <div className="px-6 py-4 border-b border-gray-200">
                            <form onSubmit={handleCreateAdmin} className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            First Name *
                                        </label>
                                        <input
                                            type="text"
                                            name="firstName"
                                            value={formData.firstName}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded-md ${
                                                errors.firstName ? 'border-red-300' : 'border-gray-300'
                                            }`}
                                        />
                                        {errors.firstName && (
                                            <p className="text-sm text-red-600">{errors.firstName}</p>
                                        )}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Last Name *
                                        </label>
                                        <input
                                            type="text"
                                            name="lastName"
                                            value={formData.lastName}
                                            onChange={handleInputChange}
                                            className={`w-full px-3 py-2 border rounded-md ${
                                                errors.lastName ? 'border-red-300' : 'border-gray-300'
                                            }`}
                                        />
                                        {errors.lastName && (
                                            <p className="text-sm text-red-600">{errors.lastName}</p>
                                        )}
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Email *
                                    </label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                        className={`w-full px-3 py-2 border rounded-md ${
                                            errors.email ? 'border-red-300' : 'border-gray-300'
                                        }`}
                                    />
                                    {errors.email && (
                                        <p className="text-sm text-red-600">{errors.email}</p>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Company *
                                    </label>
                                    <input
                                        type="text"
                                        name="company"
                                        value={formData.company}
                                        onChange={handleInputChange}
                                        className={`w-full px-3 py-2 border rounded-md ${
                                            errors.company ? 'border-red-300' : 'border-gray-300'
                                        }`}
                                    />
                                    {errors.company && (
                                        <p className="text-sm text-red-600">{errors.company}</p>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Password *
                                    </label>
                                    <input
                                        type="password"
                                        name="password"
                                        value={formData.password}
                                        onChange={handleInputChange}
                                        className={`w-full px-3 py-2 border rounded-md ${
                                            errors.password ? 'border-red-300' : 'border-gray-300'
                                        }`}
                                    />
                                    {errors.password && (
                                        <p className="text-sm text-red-600">{errors.password}</p>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        type="submit"
                                        disabled={isLoading}
                                        className="bg-[#1e40af] text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                                    >
                                        {isLoading ? 'Creating...' : 'Create Admin'}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowCreateForm(false);
                                            resetForm();
                                        }}
                                        className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        User
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Company
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Role
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Created
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {users.map((user) => (
                                    <tr key={user.id}>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div>
                                                <div className="text-sm font-medium text-gray-900">
                                                    {user.firstName} {user.lastName}
                                                </div>
                                                <div className="text-sm text-gray-500">{user.email}</div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {user.company}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getRoleBadge(user.role)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(user.createdAt).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            {user.role !== 'super-admin' && (
                                                <div className="flex gap-2">
                                                    {user.role === 'admin' ? (
                                                        <button
                                                            onClick={() => handleUpdateRole(user.id, 'user')}
                                                            className="text-blue-600 hover:text-blue-900"
                                                        >
                                                            Demote to User
                                                        </button>
                                                    ) : (
                                                        <button
                                                            onClick={() => handleUpdateRole(user.id, 'admin')}
                                                            className="text-green-600 hover:text-green-900"
                                                        >
                                                            Promote to Admin
                                                        </button>
                                                    )}
                                                    <button
                                                        onClick={() => handleDeleteUser(user.id)}
                                                        className="text-red-600 hover:text-red-900 flex items-center gap-1"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                        Delete
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
} 