import { useState } from 'react';
import { Search, BookOpen, Clock, ChevronRight, XCircle, AlertTriangle } from 'lucide-react';
import Header from '../components/layout/Header';
interface RegulatoryFramework {
    code: string;
    name: string;
    jurisdiction: string;
    type: string;
    applicableContracts: string[];
    keyProvisions: Record<string, string>;
    penalties?: Record<string, string>;
    recentUpdates?: string[];
}

// Mock data
const mockRegulatoryFrameworks: RegulatoryFramework[] = [
    {
        code: 'GDPR',
        name: 'General Data Protection Regulation',
        jurisdiction: 'EU',
        type: 'Data Privacy',
        applicableContracts: ['Data Processing Agreement', 'Employment Contract', 'Service Agreement'],
        keyProvisions: {
        'Art. 5': 'Principles relating to processing of personal data',
        'Art. 6': 'Lawfulness of processing',
        },
        penalties: {
        'Lower Tier': 'Up to €10 million or 2% of annual global turnover',
        },
        recentUpdates: ['2023-01-10: Cookie consent guidance update'],
    },
    {
        code: 'PDPA SG',
        name: 'Personal Data Protection Act (Singapore)',
        jurisdiction: 'SG',
        type: 'Data Privacy',
        applicableContracts: ['NDA', 'Service Agreement'],
        keyProvisions: {
        'Section 12': 'Consent obligation',
        },
        penalties: {
        'Max Fine': 'Up to S$1 million or 10% of turnover',
        },
        recentUpdates: ['2021-02-01: Breach notification requirement'],
    },
];

export default function RegulatoryLibrary() {
    const [search, setSearch] = useState('');
    const [jurisdiction, setJurisdiction] = useState('');
    const [type, setType] = useState('');
    const [modalReg, setModalReg] = useState<RegulatoryFramework | null>(null);

    const filtered = mockRegulatoryFrameworks.filter((r) => {
        const matchesSearch = r.name.toLowerCase().includes(search.toLowerCase());
        const matchesJurisdiction = !jurisdiction || r.jurisdiction === jurisdiction;
        const matchesType = !type || r.type === type;
        return matchesSearch && matchesJurisdiction && matchesType;
    });

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 to-slate-950 text-gray-100">
        <Header />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10 mt-10 p-6">
            {/* Search bar */}
            <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
            <input
                className="w-full bg-slate-800 border border-slate-600 rounded-md py-2 pl-10 pr-3 text-sm placeholder-gray-400"
                placeholder="Search by law or keyword..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
            />
            </div>
            {/* Filter */}
            <select
            className="bg-slate-800 border border-slate-600 rounded-md py-2 px-3 text-sm"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            >
            <option value="">All Jurisdictions</option>
            <option value="EU">EU</option>
            <option value="SG">Singapore</option>
            </select>
            <select
            className="bg-slate-800 border border-slate-600 rounded-md py-2 px-3 text-sm"
            value={type}
            onChange={(e) => setType(e.target.value)}
            >
            <option value="">All Types</option>
            <option value="Data Privacy">Data Privacy</option>
            </select>
        </div>

        {/* Regulations cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
            {filtered.length > 0 ? (
            filtered.map((reg) => (
                <div
                key={reg.code}
                onClick={() => setModalReg(reg)}
                className="bg-slate-800 p-6 rounded-lg border border-slate-700 hover:border-blue-500 hover:shadow-xl cursor-pointer transition-transform transform hover:scale-105"
                >
                <div className="flex items-center gap-2 mb-2">
                    <BookOpen className="text-blue-300 w-5 h-5" />
                    <h3 className="text-lg font-semibold">{reg.name}</h3>
                </div>
                <p className="text-sm text-gray-300 mb-1">Jurisdiction: <span className="text-white">{reg.jurisdiction}</span></p>
                <p className="text-sm text-gray-300 mb-1">Type: <span className="text-white">{reg.type}</span></p>
                <p className="text-xs text-gray-400">{Object.values(reg.keyProvisions)[0] ?? 'No provisions listed'}...</p>
                <div className="flex justify-end mt-3 text-blue-400 text-sm">
                    View Details <ChevronRight className="w-4 h-4" />
                </div>
                </div>
            ))
            ) : (
            <p className="col-span-full text-center text-gray-400">No regulations match your filters.</p>
            )}
        </div>

        {modalReg && (
            <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 w-full max-w-2xl rounded-lg p-6 border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-white">{modalReg.name}</h2>
                <XCircle className="text-gray-400 w-6 h-6 cursor-pointer" onClick={() => setModalReg(null)} />
                </div>
                <p className="text-sm text-gray-300 mb-2">Jurisdiction: <span className="text-white">{modalReg.jurisdiction}</span></p>
                <p className="text-sm text-gray-300 mb-2">Type: <span className="text-white">{modalReg.type}</span></p>

                <div className="mb-4">
                <h3 className="text-blue-300 font-semibold mb-2">Key Provisions</h3>
                <ul className="text-sm space-y-1">
                    {Object.entries(modalReg.keyProvisions).map(([k, v]) => (
                    <li key={k}><strong>{k}:</strong> {v}</li>
                    ))}
                </ul>
                </div>

                {modalReg.penalties && (
                <div className="mb-4">
                    <h3 className="text-red-300 font-semibold flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4" /> Penalties
                    </h3>
                    <ul className="text-sm space-y-1">
                    {Object.entries(modalReg.penalties).map(([k, v]) => (
                        <li key={k}><strong>{k}:</strong> {v}</li>
                    ))}
                    </ul>
                </div>
                )}

                {modalReg.recentUpdates && (
                <div>
                    <h3 className="text-blue-300 font-semibold flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4" /> Recent Updates
                    </h3>
                    <ul className="list-disc pl-5 text-sm space-y-1">
                    {modalReg.recentUpdates.map((u, i) => (
                        <li key={i}>{u}</li>
                    ))}
                    </ul>
                </div>
                )}
            </div>
            </div>
        )}
        </div>
    );
}
