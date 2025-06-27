import { Link } from 'react-router-dom';
import { FileText } from 'lucide-react';

export default function Header() {
    return (
        <header className="w-full sticky top-0 z-50 bg-gradient-to-br from-[#1e40af] to-slate-900 backdrop-blur-sm bg-opacity-90 shadow-2xl">
            <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-20">
                <div className="flex items-center gap-3">
                    <div className="bg-[#1e40af] w-10 h-10 flex items-center justify-center rounded-md shadow-lg">
                        <FileText className="text-white w-6 h-6" />
                    </div>
                    <Link to="/" className="text-2xl font-bold text-white tracking-wide hover:text-blue-200 transition-colors duration-200">
                        LegalGuard
                    </Link>
                </div>

                <nav className="hidden md:flex items-center gap-7 text-sm font-medium">
                    <Link to="/" className="text-gray-300 hover:text-blue-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                        Dashboard
                    </Link>
                    <Link to="/analyze" className="text-gray-300 hover:text-blue-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                        Analyze
                    </Link>
                    <Link to="/compliance" className="text-gray-300 hover:text-blue-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                        Compliance
                    </Link>
                    <Link to="/regulations" className="text-gray-300 hover:text-blue-300 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                        Regulations
                    </Link>
                </nav>

                <div className="flex items-center gap-3">
                    <Link to="/login" className="text-blue-300 hover:bg-blue-800/30 px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 border border-transparent hover:border-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                        Sign In
                    </Link>
                    <Link to="/signup" className="bg-[#1e40af] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-800 transition-colors duration-200 shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                        Register
                    </Link>
                </div>
            </div>
        </header>
    );
}
