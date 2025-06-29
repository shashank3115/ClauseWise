import { Link, useNavigate } from 'react-router-dom';
import { FileText, LogOut, Crown, Shield, Users, Settings } from 'lucide-react';
import { authService } from '../../utils/auth';
import { useState } from 'react';

export default function Header() {
    const navigate = useNavigate();
    const [showDropdown, setShowDropdown] = useState(false);
    const currentUser = authService.getCurrentUser();
    const isAuthenticated = authService.isAuthenticated();

    const handleLogout = () => {
        authService.logout();
        navigate('/');
    };

    const getRoleBadge = (role: string) => {
        const baseClasses = "px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1";
        
        switch (role) {
            case 'super-admin':
                return (
                    <span className={`${baseClasses} bg-red-100 text-red-800`}>
                        <Crown className="w-3 h-3" />
                        Super Admin
                    </span>
                );
            case 'admin':
                return (
                    <span className={`${baseClasses} bg-blue-100 text-blue-800`}>
                        <Shield className="w-3 h-3" />
                        Admin
                    </span>
                );
            default:
                return (
                    <span className={`${baseClasses} bg-gray-100 text-gray-800`}>
                        <Users className="w-3 h-3" />
                        User
                    </span>
                );
        }
    };

    if (!isAuthenticated) {
        return (
            <header className="w-full sticky top-0 z-50 bg-gradient-to-br from-[#1e40af] to-slate-900 backdrop-blur-sm bg-opacity-90 shadow-2xl">
                <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-20">
                    <div className="flex items-center gap-3">
                        <div className="bg-[#1e40af] w-10 h-10 flex items-center justify-center rounded-md shadow-lg">
                            <FileText className="text-white w-6 h-6" />
                        </div>
                        <Link
                            to="/"
                            className="text-2xl font-bold text-white tracking-wide hover:text-blue-200 transition-colors duration-200"
                        >
                            LegalGuard
                        </Link>
                    </div>

                    <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
                        <Link to="/compliance" className="text-gray-300 hover:text-blue-300">Compliance</Link>
                        <Link to="/regulations" className="text-gray-300 hover:text-blue-300">Regulations</Link>
                    </nav>

                    <div className="flex items-center gap-3">
                        <Link
                            to="/login"
                            className="text-blue-300 hover:bg-blue-800/30 px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 border border-transparent hover:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                        >
                            Sign In
                        </Link>
                        <Link
                            to="/signup"
                            className="bg-[#1e40af] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition-colors duration-200 shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                        >
                            Register
                        </Link>
                    </div>
                </div>
            </header>
        );
    }

    return (
        <header className="w-full sticky top-0 z-50 bg-gradient-to-br from-[#1e40af] to-slate-900 backdrop-blur-sm bg-opacity-90 shadow-2xl">
            <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-20">
                <div className="flex items-center gap-3">
                    <div className="bg-[#1e40af] w-10 h-10 flex items-center justify-center rounded-md shadow-lg">
                        <FileText className="text-white w-6 h-6" />
                    </div>
                    <Link
                        to="/dashboard"
                        className="text-2xl font-bold text-white tracking-wide hover:text-blue-200 transition-colors duration-200"
                    >
                        LegalGuard
                    </Link>
                </div>

                <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
                    <Link to="/dashboard" className="text-gray-300 hover:text-blue-300">Dashboard</Link>
                    <Link to="/analyze" className="text-gray-300 hover:text-blue-300">Analyze</Link>
                    <Link to="/bulk-analyze" className="text-gray-300 hover:text-blue-300">Bulk Analysis</Link>
                    <Link to="/ai-insights" className="text-gray-300 hover:text-blue-300">AI Insights</Link>
                    <Link to="/compliance" className="text-gray-300 hover:text-blue-300">Compliance</Link>
                    <Link to="/regulations" className="text-gray-300 hover:text-blue-300">Regulations</Link>
                    <Link to="/reports" className="text-gray-300 hover:text-blue-300">Reports</Link>
                    {authService.hasRole('super-admin') && (
                        <Link to="/admin" className="text-gray-300 hover:text-blue-300">Admin</Link>
                    )}
                </nav>

                <div className="flex items-center gap-3">
                    <div className="hidden md:block">
                        {getRoleBadge(currentUser?.role || 'user')}
                    </div>
                    
                    <div className="relative">
                        <button
                            onClick={() => setShowDropdown(!showDropdown)}
                            className="flex items-center gap-2 text-white hover:text-blue-200 transition-colors duration-200"
                        >
                            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                                {currentUser?.firstName?.charAt(0)}{currentUser?.lastName?.charAt(0)}
                            </div>
                            <span className="hidden md:block text-sm font-medium">
                                {currentUser?.firstName} {currentUser?.lastName}
                            </span>
                        </button>

                        {showDropdown && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                                <div className="px-4 py-2 border-b border-gray-200">
                                    <p className="text-sm font-medium text-gray-900">
                                        {currentUser?.firstName} {currentUser?.lastName}
                                    </p>
                                    <p className="text-xs text-gray-500">{currentUser?.email}</p>
                                    <div className="mt-1">
                                        {getRoleBadge(currentUser?.role || 'user')}
                                    </div>
                                </div>
                                
                                <Link
                                    to="/settings"
                                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    onClick={() => setShowDropdown(false)}
                                >
                                    <Settings className="w-4 h-4" />
                                    Settings
                                </Link>
                                
                                {authService.hasRole('super-admin') && (
                                    <Link
                                        to="/admin"
                                        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        onClick={() => setShowDropdown(false)}
                                    >
                                        <Crown className="w-4 h-4" />
                                        Admin Panel
                                    </Link>
                                )}
                                
                                <button
                                    onClick={() => {
                                        handleLogout();
                                        setShowDropdown(false);
                                    }}
                                    className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                                >
                                    <LogOut className="w-4 h-4" />
                                    Sign Out
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
