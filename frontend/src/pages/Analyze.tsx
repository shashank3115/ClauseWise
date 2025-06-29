import { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, CheckCircle, XCircle, Info, File } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import { getJurisdictions } from '../services/regulatoryService';
import { analyzeContractFile } from '../services/contractService';

type FileWithMeta = File & {
    status: 'pending' | 'uploaded' | 'failed';
    analysisId?: string;
};

export default function Analyze() {
    const [file, setFile] = useState<FileWithMeta | null>(null);
    const [jurisdiction, setJurisdiction] = useState('');
    const [jurisdictions, setJurisdictions] = useState<{ code: string; name: string }[]>([]);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'complete' | 'error'>('idle');
    const [progress, setProgress] = useState(0);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchJurisdictions = async () => {
            try {
                const response = await getJurisdictions();
                console.log("Fetched jurisdictions:", response);

                const codes: string[] = response?.data?.jurisdictions ?? [];

                const JURISDICTION_NAMES: Record<string, string> = {
                    MY: 'Malaysia',
                    SG: 'Singapore',
                    EU: 'European Union',
                    US: 'United States'
                };

                const formatted = codes.map(code => ({
                    code,
                    name: JURISDICTION_NAMES[code] || code,
                }));

                setJurisdictions(formatted);
            } catch (error) {
                console.error('Failed to fetch jurisdictions:', error);
            }
        };

        fetchJurisdictions();
    }, []);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
        const uploaded = Object.assign(acceptedFiles[0], { status: 'pending' }) as FileWithMeta;
        setFile(uploaded);
        setStatus('idle');
        setProgress(0);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: false,
        accept: {
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'text/plain': ['.txt'],
        },
    });

    const removeFile = () => {
        setFile(null);
    };

    // Analyzing file (upload file, select choice)
    const handleAnalyze = async () => {
        if (!file || !jurisdiction) {
            alert('Please fill all fields and upload a file.');
            return;
        }

        setStatus('uploading');
        setProgress(10);

        try {
            await new Promise((res) => setTimeout(res, 500));
            setProgress(30);

            const formData = new FormData();
            formData.append('file', file);
            formData.append('jurisdiction', jurisdiction);

            const response = await analyzeContractFile(formData);
            file.status = 'uploaded';
            setStatus('analyzing');
            setProgress(70);

            const result = response.data;
            console.log('Analysis result:', result);

            const analysisId = `ANALYSIS-${Math.floor(Math.random() * 10000)}`;
            file.analysisId = analysisId;

            localStorage.setItem(`analysis-${analysisId}`, JSON.stringify(result));

            setProgress(100);
            setStatus('complete');

            setTimeout(() => {
            navigate(`/analysis/${analysisId}`);
            }, 1000);
        } catch (err) {
            console.error('Error during analysis:', err);
            setStatus('error');
            setProgress(0);
            file.status = 'failed';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-slate-950 text-gray-100 font-sans antialiased">
        <Header />

        <main className="max-w-5xl mx-auto py-16 px-4">
            <h1 className="text-3xl font-bold mb-6 text-center">Contract Upload & Analysis</h1>
            {/* Upload file section */}
            <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-10 text-center transition-all ${
                isDragActive
                ? 'border-blue-500 bg-blue-900/10'
                : 'border-slate-600 hover:border-blue-500 hover:bg-slate-700/20'
            }`}
            >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 mx-auto text-blue-400" />
            <p className="text-lg mt-2">Drag & drop a file here or click to upload</p>
            <p className="text-sm text-gray-400">PDF, DOCX, TXT (max 5MB)</p>
            </div>

            {file && (
            <div className="mt-6">
                <h2 className="text-xl font-semibold text-blue-300 mb-3">Uploaded File:</h2>
                <div className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                    <File className="w-4 h-4 text-gray-400" />
                    <span>{file.name}</span>
                    <span className="text-xs text-gray-500">({(file.size / 1024).toFixed(2)} KB)</span>
                    {file.status === 'uploaded' && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {file.status === 'failed' && <XCircle className="w-4 h-4 text-red-500" />}
                </div>
                <button onClick={removeFile} className="text-red-400 hover:text-red-600">
                    <XCircle className="w-5 h-5" />
                </button>
                </div>
            </div>
            )}

            <div className="mt-8">
            {/* Select jurisdiction */}
            <div>
                <label className="block text-sm font-medium text-blue-300 mb-2">Jurisdiction</label>
                <select
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white"
                    >
                    <option value="">Select jurisdiction</option>
                    {jurisdictions.map((j) => (
                        <option key={j.code} value={j.code}>
                        {j.name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Select contract type */}
            {/* <div>
                <label className="block text-sm font-medium text-blue-300 mb-2">Contract Type</label>
                <select
                value={contractType}
                onChange={(e) => setContractType(e.target.value)}
                className="w-full p-3 bg-slate-700 border border-slate-600 rounded text-white"
                >
                <option value="">Select contract type</option>
                {contractTypes.map((type) => (
                    <option key={type} value={type}>
                    {type}
                    </option>
                ))}
                </select>
            </div> */}
        </div>

            {/* Status */}
            {status !== 'idle' && (
            <div className="mt-10 bg-slate-800 p-4 rounded-lg border border-slate-600">
                <div className="flex items-center gap-3 mb-2">
                {status === 'uploading' && <Upload className="w-5 h-5 animate-bounce text-blue-400" />}
                {status === 'analyzing' && <Info className="w-5 h-5 animate-pulse text-yellow-400" />}
                {status === 'complete' && <CheckCircle className="w-5 h-5 text-green-500" />}
                {status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
                <span className="capitalize">{status}</span>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2.5">
                <div
                    className="bg-blue-500 h-2.5 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                />
                </div>
            </div>
            )}

            <div className="mt-8 text-center">
            <button
                onClick={handleAnalyze}
                disabled={!file || !jurisdiction || status === 'uploading' || status === 'analyzing'}
                className="bg-blue-700 hover:bg-blue-800 px-6 py-3 rounded-md text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
                {status === 'uploading'
                ? 'Uploading...'
                : status === 'analyzing'
                ? 'Analyzing...'
                : 'Start Analysis'}
            </button>
            </div>
        </main>
    </div>
    );
}
