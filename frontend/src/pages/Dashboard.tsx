import { FileText, Gauge, AlertCircle, Upload, FileSearch, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
    // Replace with backend data
    const stats = [
        { title: "Contracts Analyzed", value: "142", icon: <FileText className="w-5 h-5" />, trend: "up" },
        { title: "Compliance Rate", value: "87%", icon: <Gauge className="w-5 h-5" />, trend: "up" },
        { title: "Alerts Detected", value: "23", icon: <AlertCircle className="w-5 h-5" />, trend: "down" }
    ];

    // Replace with backend data
    const recentActivities = [
        { id: 1, contract: "Employment Agreement", time: "10 mins ago", risk: "medium" },
        { id: 2, contract: "NDA with TechCorp", time: "2 hours ago", risk: "low" },
        { id: 3, contract: "Data Processing Addendum", time: "1 day ago", risk: "high" }
    ];

    return (
    <div className="min-h-screen bg-gray-50">
        {/* Navigations add here */}
        <nav className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <div className="flex-shrink-0 flex items-center">
                            <div className="w-8 h-8 rounded-md flex items-center justify-center">
                                <FileText className="w-5 h-5 text-white" />
                            </div>
                            <span className="ml-2 text-xl font-bold text-gray-900">LegalGuard</span>
                        </div>
                    </div>

                    {/* Navigation links here (middle) */}

                    <div className="flex items-center ml-6">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-r from-[#1e40af] to-[#3b82f6] flex items-center justify-center text-white font-medium">
                            AU
                            {/* User icon here maybe */}
                        </div>
                    </div>
                </div>
            </div>
        </nav>

        {/* Hero Section */}
        <div className="w-full bg-gradient-to-r from-[#1e40af] to-[#3b82f6]">
            <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
                <div className="text-center">
                    <h1 className="text-4xl font-bold text-white mb-4">Streamline Your Legal Compliance</h1>
                    <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
                        Automated contract analysis and regulatory compliance monitoring across multiple jurisdictions
                    </p>
                    {/* Maybe some actions here */}
                </div>
            </div>
        </div>

        {/* Main section */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            {/* Quick stats cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                {stats.map((stat, index) => (
                    <div key={index} className="bg-white p-6 rounded-xl shadow-md border border-gray-100 hover:shadow-lg transition-shadow">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-lg bg-blue-50 text-[#1e40af]">
                                    {stat.icon}
                                </div>
                                <div>
                                    <p className="text-gray-500 text-sm font-medium">{stat.title}</p>
                                    <p className="text-3xl font-bold mt-1">{stat.value}</p>
                                </div>
                            </div>
                            {stat.trend === "up" ? (
                                <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                                    ↑ 12%
                                </span>
                            ) : (
                            <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                                ↓ 5%
                            </span>
                        )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Recent activity feed */}
            <div className="bg-white rounded-xl shadow-md overflow-hidden mb-12">
                <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold">Recent Activity</h2>
                        <Link to="/activity" className="text-[#1e40af] hover:underline flex items-center gap-1">
                            View all <ChevronRight className="w-4 h-4" />
                            {/* Do we want to view all? */}
                        </Link>
                    </div>
                </div>
                <div className="divide-y divide-gray-100">
                    {recentActivities.map(activity => (
                        <div key={activity.id} className="p-6 hover:bg-gray-50 transition-colors">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-lg ${
                                        activity.risk === 'high' ? 'bg-red-100 text-red-600' :
                                        activity.risk === 'medium' ? 'bg-amber-100 text-amber-600' :'bg-green-100 text-green-600'
                                    }`}>
                                        <FileText className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="font-medium">{activity.contract}</p>
                                        <p className="text-sm text-gray-500 mt-1">{activity.time}</p>
                                    </div>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                                    activity.risk === 'high' ? 'bg-red-100 text-red-800' :
                                    activity.risk === 'medium' ? 'bg-amber-100 text-amber-800' :'bg-green-100 text-green-800'
                                    }`}>
                                        {activity.risk} risk
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Quick actions section/buttons */}
            <div>
                <h2 className="text-xl font-semibold mb-6">Quick Actions</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <Link to="/analyze" className="bg-white p-6 rounded-xl shadow-md border border-gray-200 hover:shadow-lg transition-all flex items-center gap-4 group">
                        <div className="p-3 rounded-lg bg-blue-100 text-[#1e40af] group-hover:bg-blue-200 transition-colors">
                            <Upload className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-medium text-lg">Upload Contract</h3>
                            <p className="text-gray-500 mt-1">Analyze a single contract document</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-400 ml-auto" />
                    </Link>
                    <Link to="/reports" className="bg-white p-6 rounded-xl shadow-md border border-gray-200 hover:shadow-lg transition-all flex items-center gap-4 group">
                        <div className="p-3 rounded-lg bg-purple-100 text-purple-600 group-hover:bg-purple-200 transition-colors">
                            <FileSearch className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-medium text-lg">View Reports</h3>
                            <p className="text-gray-500 mt-1">Access your compliance reports</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-400 ml-auto" />
                    </Link>
                </div>
            </div>
        </main>
    </div>
    );
}