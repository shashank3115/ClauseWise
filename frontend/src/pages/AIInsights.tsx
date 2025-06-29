import { useState } from 'react';
import { Brain, FileText, AlertCircle, CheckCircle, Loader2, MessageSquare, Shield, Lightbulb } from 'lucide-react';
import Header from '../components/layout/Header';
import { aiInsightsService } from '../services/aiInsightsService';
import type { DocumentSummaryResponse, ClauseExplanationResponse } from '../services/aiInsightsService';

export default function AIInsights() {
    const [activeTab, setActiveTab] = useState<'summarize' | 'explain'>('summarize');
    const [documentText, setDocumentText] = useState('');
    const [clauseText, setClauseText] = useState('');
    const [summaryResult, setSummaryResult] = useState<DocumentSummaryResponse | null>(null);
    const [clauseResult, setClauseResult] = useState<ClauseExplanationResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSummarize = async () => {
        if (!documentText.trim() || documentText.length < 100) {
            setError('Please enter at least 100 characters of document text');
            return;
        }

        setIsLoading(true);
        setError(null);
        setSummaryResult(null);

        try {
            const result = await aiInsightsService.summarizeDocument({
                text: documentText,
                summary_type: 'plain_language'
            });
            setSummaryResult(result);
        } catch (err: any) {
            if (err.response?.status === 503) {
                setError('AI service is temporarily unavailable or the document is too long. Please try with a shorter document or try again later.');
            } else {
                setError(err.response?.data?.detail || 'Failed to summarize document');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleExplainClause = async () => {
        if (!clauseText.trim() || clauseText.length < 10) {
            setError('Please enter at least 10 characters of clause text');
            return;
        }

        setIsLoading(true);
        setError(null);
        setClauseResult(null);

        try {
            const result = await aiInsightsService.explainClause({
                clause_text: clauseText
            });
            setClauseResult(result);
        } catch (err: any) {
            if (err.response?.status === 503) {
                setError('AI service is temporarily unavailable or the clause is too complex. Please try with a shorter clause or try again later.');
            } else {
                setError(err.response?.data?.detail || 'Failed to explain clause');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const getRiskLevelColor = (riskLevel: string) => {
        switch (riskLevel.toLowerCase()) {
            case 'high':
                return 'text-red-400 bg-red-900/20 border-red-700';
            case 'medium':
                return 'text-yellow-400 bg-yellow-900/20 border-yellow-700';
            case 'low':
                return 'text-green-400 bg-green-900/20 border-green-700';
            default:
                return 'text-gray-400 bg-gray-900/20 border-gray-700';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-slate-950 text-gray-100">
            <Header />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Page Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-blue-900/60 rounded-xl">
                            <Brain className="w-8 h-8 text-blue-300" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">AI Insights</h1>
                            <p className="text-gray-300">Get AI-powered summaries and explanations for legal documents</p>
                        </div>
                    </div>
                </div>

                {/* Tab Navigation */}
                <div className="mb-8">
                    <div className="border-b border-slate-700">
                        <nav className="flex space-x-8">
                            <button
                                onClick={() => setActiveTab('summarize')}
                                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                                    activeTab === 'summarize'
                                        ? 'border-blue-500 text-blue-400'
                                        : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                                }`}
                            >
                                <div className="flex items-center gap-2">
                                    <FileText className="w-4 h-4" />
                                    Document Summary
                                </div>
                            </button>
                            <button
                                onClick={() => setActiveTab('explain')}
                                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                                    activeTab === 'explain'
                                        ? 'border-blue-500 text-blue-400'
                                        : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
                                }`}
                            >
                                <div className="flex items-center gap-2">
                                    <MessageSquare className="w-4 h-4" />
                                    Clause Explanation
                                </div>
                            </button>
                        </nav>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="mb-6 p-4 bg-red-900/20 border border-red-700 rounded-lg flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-red-300">{error}</p>
                    </div>
                )}

                {/* Document Summary Tab */}
                {activeTab === 'summarize' && (
                    <div className="grid lg:grid-cols-2 gap-8">
                        {/* Input Section */}
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-xl font-semibold text-blue-300 mb-4">Document Text</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Paste your legal document text (minimum 100 characters)
                                    </label>
                                    <textarea
                                        value={documentText}
                                        onChange={(e) => setDocumentText(e.target.value)}
                                        placeholder="Paste your legal document text here..."
                                        className="w-full h-64 px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                    />
                                    <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
                                        <span>{documentText.length} characters</span>
                                        <span className={documentText.length >= 100 ? 'text-green-400' : 'text-red-400'}>
                                            {documentText.length >= 100 ? '✓ Ready' : `Need ${100 - documentText.length} more characters`}
                                        </span>
                                    </div>
                                </div>
                                <button
                                    onClick={handleSummarize}
                                    disabled={isLoading || documentText.length < 100}
                                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Generating Summary...
                                        </>
                                    ) : (
                                        <>
                                            <Brain className="w-4 h-4" />
                                            Summarize Document
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Results Section */}
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-xl font-semibold text-blue-300 mb-4">AI Summary</h3>
                            {summaryResult ? (
                                <div className="space-y-6">
                                    {/* Summary */}
                                    <div>
                                        <h4 className="text-lg font-medium text-white mb-2">Summary</h4>
                                        <p className="text-gray-300 leading-relaxed bg-slate-900 p-4 rounded-lg">
                                            {summaryResult.summary}
                                        </p>
                                    </div>

                                    {/* Key Points */}
                                    {summaryResult.key_points.length > 0 && (
                                        <div>
                                            <h4 className="text-lg font-medium text-white mb-2">Key Points</h4>
                                            <div className="space-y-2">
                                                {summaryResult.key_points.map((point, index) => (
                                                    <div key={index} className="flex items-start gap-3 bg-slate-900 p-3 rounded-lg">
                                                        <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                                                        <span className="text-gray-300 text-sm">{point}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Metadata */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-slate-900 p-4 rounded-lg">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Shield className="w-4 h-4 text-blue-400" />
                                                <span className="text-sm font-medium text-gray-300">Risk Level</span>
                                            </div>
                                            <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${getRiskLevelColor(summaryResult.risk_level)}`}>
                                                {summaryResult.risk_level}
                                            </span>
                                        </div>
                                        <div className="bg-slate-900 p-4 rounded-lg">
                                            <div className="flex items-center gap-2 mb-1">
                                                <FileText className="w-4 h-4 text-green-400" />
                                                <span className="text-sm font-medium text-gray-300">Word Reduction</span>
                                            </div>
                                            <span className="text-lg font-bold text-green-400">
                                                {summaryResult.word_count_reduction}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-12">
                                    <Brain className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                                    <p className="text-gray-400">
                                        Enter document text and click "Summarize Document" to get started
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Clause Explanation Tab */}
                {activeTab === 'explain' && (
                    <div className="grid lg:grid-cols-2 gap-8">
                        {/* Input Section */}
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-xl font-semibold text-blue-300 mb-4">Legal Clause</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Enter the legal clause you want explained (minimum 10 characters)
                                    </label>
                                    <textarea
                                        value={clauseText}
                                        onChange={(e) => setClauseText(e.target.value)}
                                        placeholder="Paste the legal clause here..."
                                        className="w-full h-40 px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                    />
                                    <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
                                        <span>{clauseText.length} characters</span>
                                        <span className={clauseText.length >= 10 ? 'text-green-400' : 'text-red-400'}>
                                            {clauseText.length >= 10 ? '✓ Ready' : `Need ${10 - clauseText.length} more characters`}
                                        </span>
                                    </div>
                                </div>
                                <button
                                    onClick={handleExplainClause}
                                    disabled={isLoading || clauseText.length < 10}
                                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
                                >
                                    {isLoading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Explaining Clause...
                                        </>
                                    ) : (
                                        <>
                                            <MessageSquare className="w-4 h-4" />
                                            Explain Clause
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Results Section */}
                        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                            <h3 className="text-xl font-semibold text-blue-300 mb-4">Plain English Explanation</h3>
                            {clauseResult ? (
                                <div className="space-y-6">
                                    {/* Plain English Explanation */}
                                    <div>
                                        <h4 className="text-lg font-medium text-white mb-2">What it means</h4>
                                        <p className="text-gray-300 leading-relaxed bg-slate-900 p-4 rounded-lg">
                                            {clauseResult.plain_english}
                                        </p>
                                    </div>

                                    {/* Potential Risks */}
                                    {clauseResult.potential_risks.length > 0 && (
                                        <div>
                                            <h4 className="text-lg font-medium text-white mb-2 flex items-center gap-2">
                                                <AlertCircle className="w-5 h-5 text-red-400" />
                                                Potential Risks
                                            </h4>
                                            <div className="space-y-2">
                                                {clauseResult.potential_risks.map((risk, index) => (
                                                    <div key={index} className="flex items-start gap-3 bg-red-900/20 border border-red-700/30 p-3 rounded-lg">
                                                        <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                                                        <span className="text-red-200 text-sm">{risk}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Recommendations */}
                                    {clauseResult.recommendations.length > 0 && (
                                        <div>
                                            <h4 className="text-lg font-medium text-white mb-2 flex items-center gap-2">
                                                <Lightbulb className="w-5 h-5 text-yellow-400" />
                                                Recommendations
                                            </h4>
                                            <div className="space-y-2">
                                                {clauseResult.recommendations.map((recommendation, index) => (
                                                    <div key={index} className="flex items-start gap-3 bg-yellow-900/20 border border-yellow-700/30 p-3 rounded-lg">
                                                        <Lightbulb className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                                                        <span className="text-yellow-200 text-sm">{recommendation}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-12">
                                    <MessageSquare className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                                    <p className="text-gray-400">
                                        Enter a legal clause and click "Explain Clause" to get started
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
