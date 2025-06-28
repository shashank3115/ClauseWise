import { useState } from 'react';
import { FileText, AlertTriangle, Lightbulb, Download, CheckSquare, Gauge, XCircle, PlusCircle, ExternalLink } from 'lucide-react';
import Header from '../components/layout/Header';

// Mock Data
const mockAnalysisResult = {
    analysisId: 'ANALYSIS-7890', // Pass in id from analyze, bulk analyze page
    contractName: 'Master Service Agreement - Acme Corp. (V3.0)',
    dateAnalyzed: '2025-06-25',
    overallComplianceScore: 78,
    overallRiskSeverity: 'Medium',
    violations: [
        { id: 'V001', category: 'Data Privacy', description: 'Non-compliant data transfer clause for EU citizens.', riskLevel: 'High', regulatoryReference: 'GDPR Article 46' },
        { id: 'V002', category: 'Liability', description: 'Indemnification cap is too low based on local laws.', riskLevel: 'Medium', regulatoryReference: 'Local Contract Law MY' },
        { id: 'V003', category: 'Termination', description: 'Missing clause for termination without cause in specific scenarios.', riskLevel: 'Low', regulatoryReference: 'Industry Standard' },
    ],
    missingClauses: [
        { id: 'MC01', description: 'Force Majeure clause is absent.', recommendation: 'Add a standard Force Majeure clause tailored for current climate risks.', importance: 'High' },
        { id: 'MC02', description: 'Dispute Resolution clause lacks arbitration details.', recommendation: 'Specify arbitration rules and venue for international disputes.', importance: 'Medium' },
    ],
    recommendations: [
        { id: 'R001', description: 'Revise GDPR data transfer mechanisms with legal team.', status: 'Pending', dueDate: '2025-07-30' },
        { id: 'R002', description: 'Update indemnification limits as per legal counsel.', status: 'Pending', dueDate: '2025-08-15' },
        { id: 'R003', description: 'Conduct a review of all standard contract templates.', status: 'Completed', dueDate: '2025-06-20' },
    ],
    actionItems: [
        { id: 'A001', description: 'Schedule meeting with Legal for GDPR clause review.', completed: false },
        { id: 'A002', description: 'Draft addendum for indemnification clause.', completed: false },
        { id: 'A003', description: 'Notify relevant stakeholders about analysis findings.', completed: true },
    ]
};

export default function AnalysisResult() {
    const { analysisId, contractName, dateAnalyzed, overallComplianceScore, overallRiskSeverity, violations, missingClauses, recommendations, actionItems } = mockAnalysisResult;

    const getRiskColor = (severity: 'High' | 'Medium' | 'Low' | string) => {
        switch (severity) {
            case 'High': return 'text-red-500';
            case 'Medium': return 'text-amber-500';
            case 'Low': return 'text-green-500';
            default: return 'text-gray-400';
        }
    };

    const getRiskBgClass = (severity: 'High' | 'Medium' | 'Low' | string) => {
        switch (severity) {
            case 'High': return 'bg-red-700/30 border-red-500';
            case 'Medium': return 'bg-amber-700/30 border-amber-500';
            case 'Low': return 'bg-green-700/30 border-green-500';
            default: return 'bg-gray-700/30 border-gray-500';
        }
    };

    const [localActionItems, setLocalActionItems] = useState(actionItems);

    const toggleActionItem = (id: string) => {
        setLocalActionItems(prevItems =>
            prevItems.map(item =>
                item.id === id ? { ...item, completed: !item.completed } : item
            )
        );
    };

    const deleteActionItem = (id: string) => {
        setLocalActionItems(prevItems => prevItems.filter(item => item.id !== id));
    };

    const addActionItem = () => {
        const newItemText = prompt("Enter new action item:"); // Use custom modal in real app
        if (newItemText) {
            const newId = `A${String(localActionItems.length + 1).padStart(3, '0')}`;
            setLocalActionItems(prevItems => [...prevItems, { id: newId, description: newItemText, completed: false }]);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-slate-950 text-gray-100 font-sans antialiased">
            <Header />

            <main className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
                <h1 className="text-4xl font-extrabold text-white mb-8 text-center drop-shadow-lg">Analysis Results</h1>

                {/* Contract summary card with risk status */}
                <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-2xl font-semibold text-blue-300 flex items-center gap-2">
                            <FileText className="w-7 h-7" /> Contract Summary
                        </h2>
                        <span className="text-sm text-gray-400">Analysis ID: <span className="font-medium text-white">{analysisId}</span></span>
                    </div>
                    <p className="text-3xl font-bold text-white mb-2">{contractName}</p>
                    <p className="text-sm text-gray-400">Analyzed on: {dateAnalyzed}</p>
                    <div className="mt-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Gauge className="w-7 h-7 text-blue-400" />
                            <p className="text-lg text-gray-300">Compliance Score:</p>
                            <p className={`text-2xl font-bold ${overallComplianceScore > 80 ? 'text-green-400' : overallComplianceScore > 60 ? 'text-amber-400' : 'text-red-400'}`}>
                                {overallComplianceScore}%
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <AlertTriangle className={`w-7 h-7 ${getRiskColor(overallRiskSeverity)}`} />
                            <p className="text-lg text-gray-300">Overall Risk:</p>
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getRiskBgClass(overallRiskSeverity)} ${getRiskColor(overallRiskSeverity)}`}>
                                {overallRiskSeverity}
                            </span>
                        </div>
                    </div>
                </section>

                {/* Compliance violations */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700">
                        <h3 className="text-xl font-semibold text-red-300 mb-4 flex items-center gap-2">
                            <XCircle className="w-6 h-6" /> Compliance Violations
                        </h3>
                        {violations.length === 0 ? (
                            <p className="text-gray-400">No direct compliance violations found.</p>
                        ) : (
                            <div className="space-y-4">
                                {violations.map(violation => (
                                    <div key={violation.id} className="p-4 rounded-md bg-slate-700/50 border border-slate-600">
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="font-medium text-white">{violation.description}</p>
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getRiskBgClass(violation.riskLevel)} ${getRiskColor(violation.riskLevel)}`}>
                                                {violation.riskLevel} Risk
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400">Category: {violation.category}</p>
                                        {violation.regulatoryReference && (
                                            <p className="text-xs text-blue-400 mt-1 flex items-center gap-1">
                                                <ExternalLink className="w-3 h-3" /> Reference: <a href={`#${violation.regulatoryReference}`} className="hover:underline">{violation.regulatoryReference}</a>
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    {/* Missing clauses */}
                    <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700">
                        <h3 className="text-xl font-semibold text-amber-300 mb-4 flex items-center gap-2">
                            <XCircle className="w-6 h-6" /> Missing Clauses
                        </h3>
                        {missingClauses.length === 0 ? (
                            <p className="text-gray-400">No missing clauses identified.</p>
                        ) : (
                            <div className="space-y-4">
                                {missingClauses.map(clause => (
                                    <div key={clause.id} className="p-4 rounded-md bg-slate-700/50 border border-slate-600">
                                        <p className="font-medium text-white mb-1">{clause.description}</p>
                                        <p className="text-sm text-gray-400">Recommendation: {clause.recommendation}</p>
                                        <p className="text-xs text-gray-500 mt-1">Importance: <span className="font-semibold">{clause.importance}</span></p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                </div>

                {/* Recommendations */}
                <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 mb-8">
                    <h3 className="text-xl font-semibold text-green-300 mb-4 flex items-center gap-2">
                        <Lightbulb className="w-6 h-6" /> Recommendations
                    </h3>
                    {recommendations.length === 0 ? (
                        <p className="text-gray-400">No specific recommendations at this time.</p>
                    ) : (
                        <div className="space-y-4">
                            {recommendations.map(rec => (
                                <div key={rec.id} className="p-4 rounded-md bg-slate-700/50 border border-slate-600 flex justify-between items-center">
                                    <div>
                                        <p className="font-medium text-white">{rec.description}</p>
                                        {rec.dueDate && <p className="text-sm text-gray-400 mt-1">Due: {rec.dueDate}</p>}
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold
                                        ${rec.status === 'Completed' ? 'bg-green-700/30 text-green-300 border-green-500' :
                                        rec.status === 'Pending' ? 'bg-amber-700/30 text-amber-200 border-amber-500' :
                                        'bg-gray-700/30 text-gray-400 border-gray-500'}`}>
                                        {rec.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* Action item checklist */}
                <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 mb-8">
                    <h3 className="text-xl font-semibold text-blue-300 mb-4 flex items-center justify-between">
                        <span className="flex items-center gap-2"><CheckSquare className="w-6 h-6" /> Action Items Checklist</span>
                        <button
                            onClick={addActionItem}
                            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-1.5 px-3 rounded-md flex items-center gap-1 transition-colors duration-200"
                        >
                            <PlusCircle className="w-4 h-4" /> Add Item
                        </button>
                    </h3>
                    {localActionItems.length === 0 ? (
                        <p className="text-gray-400">No action items defined yet.</p>
                    ) : (
                        <div className="space-y-3">
                            {localActionItems.map(item => (
                                <div key={item.id} className="flex items-center justify-between bg-slate-700/50 p-3 rounded-md border border-slate-600">
                                    <label className="flex items-center flex-grow cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={item.completed}
                                            onChange={() => toggleActionItem(item.id)}
                                            className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500 transition-colors duration-200"
                                        />
                                        <span className={`ml-3 text-white ${item.completed ? 'line-through text-gray-500' : ''}`}>
                                            {item.description}
                                        </span>
                                    </label>
                                    <button
                                        onClick={() => deleteActionItem(item.id)}
                                        className="ml-4 text-red-400 hover:text-red-600 transition-colors duration-200"
                                        title="Delete action item"
                                    >
                                        <XCircle className="w-5 h-5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* Export Options */}
                <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 text-center">
                    <h2 className="text-xl font-semibold text-blue-300 mb-4 flex items-center justify-center gap-2">
                        <Download className="w-6 h-6" /> Export Options
                    </h2>
                    <p className="text-gray-300 mb-6">Download the comprehensive analysis report.</p>
                    <div className="flex justify-center gap-4">
                        <button className="bg-green-700 hover:bg-green-800 text-white font-bold py-2 px-6 rounded-md shadow-lg transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                            Download PDF Report
                        </button>
                        <button className="bg-blue-700 hover:bg-blue-800 text-white font-bold py-2 px-6 rounded-md shadow-lg transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                            Export Findings to CSV
                        </button>
                    </div>
                </section>
            </main>
        </div>
    );
}
