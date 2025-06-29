import { Link } from 'react-router-dom';
import { Shield, FileText, TrendingUp, Users, ArrowRight, CheckCircle } from 'lucide-react';
import Header from '../components/layout/Header';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Header />

      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              Streamline Your
              <span className="text-[#1e40af]"> Legal Compliance</span>
            </h1>
            <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
              AI-powered document analysis and regulatory compliance monitoring. 
              Stay ahead of legal requirements with automated risk assessment and real-time alerts.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/signup" className="bg-[#1e40af] text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center">
                Start Free Trial
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <Link to="/compliance" className="border-2 border-[#1e40af] text-[#1e40af] px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-800 transition-colors">
                Learn More
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">
              Why Choose LegalGuard?
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Comprehensive legal compliance solution designed for modern businesses
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700">
              <div className="bg-blue-900/50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 border border-blue-700/30">
                <FileText className="text-blue-400 w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Document Analysis
              </h3>
              <p className="text-gray-300">
                AI-powered analysis of contracts, policies, and legal documents with instant risk assessment
              </p>
            </div>

            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700">
              <div className="bg-green-900/50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 border border-green-700/30">
                <Shield className="text-green-400 w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Compliance Monitoring
              </h3>
              <p className="text-gray-300">
                Real-time monitoring of regulatory changes and automated compliance reporting
              </p>
            </div>

            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700">
              <div className="bg-purple-900/50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 border border-purple-700/30">
                <TrendingUp className="text-purple-400 w-8 h-8" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Risk Management
              </h3>
              <p className="text-gray-300">
                Proactive risk identification and mitigation strategies with detailed analytics
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-24 bg-gradient-to-r from-[#1e40af] to-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Compliance Process?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of companies already using LegalGuard to streamline their legal compliance
          </p>
          <Link to="/signup" className="bg-white text-[#1e40af] px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-50 transition-colors inline-flex items-center">
            Get Started Today
            <ArrowRight className="ml-2 w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <div className="bg-[#1e40af] w-8 h-8 flex items-center justify-center rounded-lg">
                  <Shield className="text-white w-5 h-5" />
                </div>
                <span className="ml-2 text-xl font-bold">LegalGuard</span>
              </div>
              <p className="text-gray-400">
                AI-powered legal compliance platform for modern businesses.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4 text-white">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link to="/compliance" className="hover:text-white transition-colors">Compliance</Link></li>
                <li><Link to="/regulations" className="hover:text-white transition-colors">Regulations</Link></li>
                <li><Link to="/signup" className="hover:text-white transition-colors">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4 text-white">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Support</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4 text-white">Legal</h3>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Cookie Policy</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 LegalGuard. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
} 