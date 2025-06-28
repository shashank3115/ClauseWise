import { useState } from 'react';
import {
    UploadCloud,
    FileText,
    CheckCircle,
    XCircle,
    Loader,
    Download,
    ExternalLink,
    Clock
} from 'lucide-react';
import Header from '../components/layout/Header.tsx';
interface FileStatus {
    name: string;
    status: 'Pending' | 'Processing' | 'Completed' | 'Failed';
    progress: number;
    analysisId?: string;
    error?: string;
}

    export default function BulkAnalyze() {
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [processingQueue, setProcessingQueue] = useState<FileStatus[]>([]);
    const [isUploading, setIsUploading] = useState(false);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
        const filesArray = Array.from(event.target.files);
        setSelectedFiles(filesArray);

        const newQueueItems = filesArray.map(file => ({
            name: file.name,
            status: 'Pending' as const,
            progress: 0
        }));
        setProcessingQueue(prev => [...prev, ...newQueueItems]);
        }
    };

    const handleUploadFiles = async () => {
        if (selectedFiles.length === 0) {
        alert('Please select files to upload first.');
        return;
        }

        setIsUploading(true);

        for (const file of selectedFiles) {
        const fileName = file.name;

        setProcessingQueue(prev =>
            prev.map(item =>
            item.name === fileName ? { ...item, status: 'Processing', progress: 0 } : item
            )
        );

        for (let p = 0; p <= 100; p += 10) {
            await new Promise(res => setTimeout(res, 100));
            setProcessingQueue(prev =>
            prev.map(item =>
                item.name === fileName ? { ...item, progress: p } : item
            )
            );
        }

        const isSuccess = Math.random() > 0.2;
        setProcessingQueue(prev =>
            prev.map(item =>
            item.name === fileName
                ? {
                    ...item,
                    status: isSuccess ? 'Completed' : 'Failed',
                    progress: 100,
                    analysisId: isSuccess
                    ? `ANALYSIS-${Math.floor(Math.random() * 10000)}`
                    : undefined,
                    error: isSuccess ? undefined : 'Analysis failed due to format error.'
                }
                : item
            )
        );
    }

    setIsUploading(false);
    setSelectedFiles([]);
    };

    const getStatusIcon = (status: FileStatus['status']) => {
        switch (status) {
        case 'Pending': return <Clock className="w-5 h-5 text-gray-400" />;
        case 'Processing': return <Loader className="w-5 h-5 text-blue-400 animate-spin" />;
        case 'Completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
        case 'Failed': return <XCircle className="w-5 h-5 text-red-500" />;
        default: return null;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-slate-950 text-gray-100 font-sans antialiased">
        <Header />

        <main className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
            <h1 className="text-4xl font-extrabold text-white mb-8 text-center drop-shadow-lg">Bulk Analysis</h1>

            {/* Upload multiple files section */}
            <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 mb-8 text-center">
            <h2 className="text-xl font-semibold text-blue-300 mb-4 flex items-center justify-center gap-2">
                <UploadCloud className="w-6 h-6" /> Upload Contracts for Batch Analysis
            </h2>

            <div className="border-2 border-dashed border-slate-600 rounded-lg p-10 cursor-pointer hover:border-blue-500 transition-colors duration-200">
                <input
                type="file"
                multiple
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
                accept=".pdf,.docx,.txt"
                />
                <label htmlFor="file-upload" className="block text-gray-400 font-medium cursor-pointer">
                Drag & drop files here, or <span className="text-blue-400 hover:underline">browse</span>
                <p className="text-sm text-gray-500 mt-1">Supported: PDF, DOCX, TXT (Max 50MB)</p>
                </label>

                {selectedFiles.length > 0 && (
                <div className="mt-4 text-left">
                    <p className="text-white font-medium">Selected Files:</p>
                    <ul className="list-disc list-inside text-gray-300">
                    {selectedFiles.map((file, idx) => <li key={idx}>{file.name}</li>)}
                    </ul>
                </div>
                )}
            </div>

            <button
                onClick={handleUploadFiles}
                disabled={selectedFiles.length === 0 || isUploading}
                className="mt-6 bg-blue-700 hover:bg-blue-800 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 flex items-center justify-center mx-auto gap-2"
            >
                {isUploading ? <Loader className="w-5 h-5 animate-spin" /> : <UploadCloud className="w-5 h-5" />}
                {isUploading ? 'Processing...' : 'Start Batch Analysis'}
            </button>
            </section>

            {/* After file is uploaded/chosen */}
            {processingQueue.length > 0 && (
            <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 mb-8">
                <h2 className="text-xl font-semibold text-blue-300 mb-4 flex items-center gap-2">
                <FileText className="w-6 h-6" /> Analysis Queue
                </h2>

                <div className="space-y-4">
                {processingQueue.map((file, index) => (
                    <div key={index} className="bg-slate-700/50 p-4 rounded-md border border-slate-600">
                    <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-white">{file.name}</span>
                        <div className="flex items-center gap-2">
                        {getStatusIcon(file.status)}
                        <span className={`text-sm font-semibold
                            ${file.status === 'Completed' ? 'text-green-400' :
                            file.status === 'Processing' ? 'text-blue-400' :
                                file.status === 'Failed' ? 'text-red-400' : 'text-gray-400'}`}>
                            {file.status}
                        </span>
                        </div>
                    </div>

                    <div className="w-full bg-slate-600 rounded-full h-2.5">
                        <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${file.progress}%` }} />
                    </div>

                    {file.error && <p className="text-red-400 text-sm mt-2">{file.error}</p>}
                    {file.analysisId && (
                        <p className="text-blue-400 text-sm mt-2">
                        Analysis ID:{' '}
                        <a href={`/analysis/${file.analysisId}`} className="hover:underline flex items-center gap-1">
                            {file.analysisId} <ExternalLink className="w-3 h-3" />
                        </a>
                        </p>
                    )}
                    </div>
                ))}
                </div>
            </section>
            )}

            {/* Export */}
            {processingQueue.some(f => f.status === 'Completed') && (
            <section className="bg-slate-800 p-6 rounded-lg shadow-2xl border border-slate-700 text-center">
                <h2 className="text-xl font-semibold text-blue-300 mb-4 flex items-center justify-center gap-2">
                <Download className="w-6 h-6" /> Bulk Export Results
                </h2>
                <p className="text-gray-300 mb-6">Download a report of all completed analyses.</p>
                <button className="bg-purple-700 hover:bg-purple-800 text-white font-bold py-2 px-6 rounded-md shadow-lg transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                Download Report (CSV/PDF)
                </button>
            </section>
            )}
        </main>
        </div>
    );
}
