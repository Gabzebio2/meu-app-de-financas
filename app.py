import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, onAuthStateChanged, signInWithCustomToken } from 'firebase/auth';
import { getFirestore, collection, doc, addDoc, getDocs, onSnapshot, updateDoc, deleteDoc, query, where, setDoc } from 'firebase/firestore';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts';
import { format, parseISO, startOfMonth, endOfMonth, subMonths, addMonths, addDays, addWeeks, addYears } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// --- Ícones (Lucide-React) ---
const Upload = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>;
const PlusCircle = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="16"/><line x1="8" x2="16" y1="12" y2="12"/></svg>;
const Folder = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.23A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>;
const Edit = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>;
const Trash2 = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>;
const ArrowLeft = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>;
const X = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>;
const ChevronDown = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m6 9 6 6 6-6"/></svg>;
const ChevronUp = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m18 15-6-6-6 6"/></svg>;
const ChevronLeft = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m15 18-6-6 6-6"/></svg>;
const ChevronRight = ({ className }) => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="m9 18 6-6-6-6"/></svg>;

// --- Configuração do Firebase ---
const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : {};
const appId = typeof __app_id !== 'undefined' ? __app_id : 'financas-yg-default';

// --- Componente Principal: App ---
export default function App() {
    const [auth, setAuth] = useState(null);
    const [db, setDb] = useState(null);
    const [userId, setUserId] = useState(null);
    const [isAuthReady, setIsAuthReady] = useState(false);
    
    const [selectedDatasetId, setSelectedDatasetId] = useState(null);

    useEffect(() => {
        const app = initializeApp(firebaseConfig);
        const authInstance = getAuth(app);
        const dbInstance = getFirestore(app);
        
        setAuth(authInstance);
        setDb(dbInstance);

        const unsubscribe = onAuthStateChanged(authInstance, async (user) => {
            if (user) {
                setUserId(user.uid);
            } else {
                try {
                    if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
                        await signInWithCustomToken(authInstance, __initial_auth_token);
                    } else {
                        await signInAnonymously(authInstance);
                    }
                } catch (error) {
                    console.error("Erro na autenticação:", error);
                }
            }
            setIsAuthReady(true);
        });

        return () => unsubscribe();
    }, []);

    if (!isAuthReady || !db || !auth) {
        return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Carregando...</div>;
    }

    if (selectedDatasetId) {
        return <Dashboard db={db} userId={userId} datasetId={selectedDatasetId} goBack={() => setSelectedDatasetId(null)} />;
    }

    return <LandingPage db={db} userId={userId} onSelectDataset={setSelectedDatasetId} />;
}


// --- Componente: LandingPage ---
function LandingPage({ db, userId, onSelectDataset }) {
    const [datasets, setDatasets] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [renamingId, setRenamingId] = useState(null);
    const [newName, setNewName] = useState("");

    const datasetsCollectionRef = useMemo(() => collection(db, 'artifacts', appId, 'public', 'data', 'datasets'), [db]);

    useEffect(() => {
        if (!userId) return;
        const q = query(datasetsCollectionRef, where("userId", "==", userId));
        const unsubscribe = onSnapshot(q, (snapshot) => {
            const fetchedDatasets = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
            setDatasets(fetchedDatasets);
        }, (error) => {
            console.error("Erro ao buscar datasets:", error);
        });
        return () => unsubscribe();
    }, [userId, datasetsCollectionRef]);

    const handleRename = async (id) => {
        if (!newName.trim()) return;
        const datasetDocRef = doc(db, 'artifacts', appId, 'public', 'data', 'datasets', id);
        try {
            await updateDoc(datasetDocRef, { name: newName });
            setRenamingId(null);
            setNewName("");
        } catch (error) {
            console.error("Erro ao renomear:", error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-4 sm:p-8">
            <div className="max-w-4xl mx-auto">
                <header className="text-center mb-12">
                    <h1 className="text-4xl sm:text-5xl font-bold text-emerald-400">Finanças YG</h1>
                    <p className="text-gray-400 mt-2">Seu painel de controle financeiro pessoal.</p>
                </header>

                <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                    <div onClick={() => setShowUploadModal(true)} className="bg-gray-800 p-8 rounded-lg shadow-lg hover:bg-gray-700 transition-all cursor-pointer flex flex-col items-center justify-center text-center">
                        <Upload className="h-16 w-16 text-emerald-400 mb-4" />
                        <h2 className="text-2xl font-semibold">Fazer Upload de Excel</h2>
                        <p className="text-gray-400 mt-2">Envie um arquivo .xlsx para começar.</p>
                    </div>
                    <div onClick={() => setShowCreateModal(true)} className="bg-gray-800 p-8 rounded-lg shadow-lg hover:bg-gray-700 transition-all cursor-pointer flex flex-col items-center justify-center text-center">
                        <PlusCircle className="h-16 w-16 text-emerald-400 mb-4" />
                        <h2 className="text-2xl font-semibold">Começar do Zero</h2>
                        <p className="text-gray-400 mt-2">Adicione suas finanças manualmente.</p>
                    </div>
                </section>

                <section>
                    <h3 className="text-2xl font-semibold mb-6 border-b-2 border-gray-700 pb-2">Meus Conjuntos de Dados</h3>
                    {datasets.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                            {datasets.map(dataset => (
                                <div key={dataset.id} className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
                                    <div className="p-5">
                                        <div className="flex items-start justify-between">
                                            <Folder className="h-8 w-8 text-emerald-400 mr-4" />
                                            {renamingId === dataset.id ? (
                                                <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)} onBlur={() => handleRename(dataset.id)} onKeyDown={(e) => e.key === 'Enter' && handleRename(dataset.id)} className="bg-gray-700 text-white text-lg font-semibold rounded px-2 py-1 w-full" autoFocus />
                                            ) : (
                                                <h4 className="text-lg font-semibold flex-grow cursor-pointer" onClick={() => onSelectDataset(dataset.id)}>{dataset.name}</h4>
                                            )}
                                            <button onClick={() => { setRenamingId(dataset.id); setNewName(dataset.name); }} className="ml-2 p-1 text-gray-400 hover:text-white"><Edit className="h-5 w-5" /></button>
                                        </div>
                                        <p className="text-sm text-gray-500 mt-2">Criado em: {dataset.createdAt?.toDate().toLocaleDateString('pt-BR')}</p>
                                    </div>
                                    <button onClick={() => onSelectDataset(dataset.id)} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 transition-colors">Abrir Painel</button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-center text-gray-500 py-8">Nenhum conjunto de dados encontrado. Crie um novo para começar.</p>
                    )}
                </section>
            </div>
            {showCreateModal && <CreateDatasetModal db={db} userId={userId} onSelectDataset={onSelectDataset} onClose={() => setShowCreateModal(false)} />}
            {showUploadModal && <UploadDatasetModal db={db} userId={userId} onSelectDataset={onSelectDataset} onClose={() => setShowUploadModal(false)} />}
        </div>
    );
}

// --- Modais para Criação e Upload ---
function CreateDatasetModal({ db, userId, onSelectDataset, onClose }) {
    const [name, setName] = useState('');
    const datasetsCollectionRef = useMemo(() => collection(db, 'artifacts', appId, 'public', 'data', 'datasets'), [db]);

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!name.trim()) return;
        try {
            const newDoc = await addDoc(datasetsCollectionRef, { name, userId, transactions: [], createdAt: new Date() });
            onSelectDataset(newDoc.id);
            onClose();
        } catch (error) {
            console.error("Erro ao criar dataset:", error);
        }
    };

    return (
        <Modal onClose={onClose} title="Criar Novo Conjunto de Dados">
            <form onSubmit={handleCreate}>
                <label htmlFor="datasetName" className="block text-sm font-medium text-gray-300 mb-2">Nome do Conjunto de Dados</label>
                <input id="datasetName" type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full input-style" placeholder="Ex: Finanças 2024" required />
                <div className="mt-6 flex justify-end gap-4">
                    <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-500 text-white font-semibold">Cancelar</button>
                    <button type="submit" className="px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold">Criar e Abrir</button>
                </div>
            </form>
        </Modal>
    );
}

const normalizeString = (str) => {
    if (typeof str !== 'string') str = String(str);
    return str.toLowerCase().trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
};
const parseCurrency = (value) => {
    if (typeof value === 'number') return value;
    if (typeof value !== 'string') return NaN;
    const cleanedValue = value.replace("R$", "").replace(/\./g, "").replace(",", ".").trim();
    return parseFloat(cleanedValue);
};
const parseDate = (value) => {
    if (value instanceof Date) return value;
    if (typeof value === 'number') return new Date(Date.UTC(1900, 0, value - 1));
    if (typeof value !== 'string') return null;
    const parts = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (parts) return new Date(Date.UTC(parts[3], parts[2] - 1, parts[1]));
    const isoDate = parseISO(value);
    if (!isNaN(isoDate.getTime())) return isoDate;
    const genericDate = new Date(value);
    return !isNaN(genericDate.getTime()) ? genericDate : null;
};

function UploadDatasetModal({ db, userId, onSelectDataset, onClose }) {
    const [name, setName] = useState('');
    const [file, setFile] = useState(null);
    const [error, setError] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [xlsx, setXlsx] = useState(null);
    const datasetsCollectionRef = useMemo(() => collection(db, 'artifacts', appId, 'public', 'data', 'datasets'), [db]);

    useEffect(() => {
        if (window.XLSX) {
            setXlsx(window.XLSX);
            return;
        }
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
        script.async = true;
        script.onload = () => setXlsx(window.XLSX);
        script.onerror = () => setError("Não foi possível carregar a biblioteca de planilhas. Verifique sua conexão com a internet.");
        document.body.appendChild(script);
        return () => { if (script.parentNode) document.body.removeChild(script); };
    }, []);

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
            setFile(selectedFile);
            setError('');
        } else {
            setFile(null);
            setError('Por favor, selecione um arquivo .xlsx');
        }
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!name.trim() || !file || !xlsx) return;
        setIsUploading(true);
        setError('');

        const reader = new FileReader();
        reader.onload = async (event) => {
            try {
                const data = event.target.result;
                const workbook = xlsx.read(data, { type: 'binary' });
                const sheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[sheetName];
                const json = xlsx.utils.sheet_to_json(worksheet, { header: 1 });

                if (json.length < 2) throw new Error("A planilha está vazia ou tem apenas cabeçalhos.");
                
                const headers = json[0].map(normalizeString);
                const requiredHeaders = ['data', 'descricao', 'categoria', 'valor'];
                const headerMap = {};
                requiredHeaders.forEach(reqHeader => {
                    const foundIndex = headers.findIndex(h => h === reqHeader);
                    if (foundIndex !== -1) headerMap[reqHeader] = json[0][foundIndex];
                });

                if (Object.keys(headerMap).length !== requiredHeaders.length) throw new Error(`O Excel deve conter as colunas: data, descrição, categoria, valor.`);

                const transactions = json.slice(1).map((row, index) => {
                    const transactionData = {};
                    json[0].forEach((header, i) => { transactionData[header] = row[i]; });
                    const valor = parseCurrency(transactionData[headerMap.valor]);
                    if (isNaN(valor)) return null;
                    const date = parseDate(transactionData[headerMap.data]);
                    if (!date || isNaN(date.getTime())) return null;
                    return { id: `${Date.now()}-${index}`, date: format(date, 'yyyy-MM-dd'), description: transactionData[headerMap.descricao]?.toString() || 'Sem descrição', category: transactionData[headerMap.categoria]?.toString() || 'Geral', amount: Math.abs(valor), type: valor >= 0 ? 'income' : 'expense' };
                }).filter(Boolean);
                
                if (transactions.length === 0) throw new Error("Nenhuma transação válida foi encontrada no arquivo. Verifique os formatos de data e valor.");

                const newDoc = await addDoc(datasetsCollectionRef, { name, userId, transactions, createdAt: new Date() });
                onSelectDataset(newDoc.id);
                onClose();

            } catch (err) {
                setError(`Erro: ${err.message}`);
                setIsUploading(false);
            }
        };
        reader.readAsBinaryString(file);
    };

    return (
        <Modal onClose={onClose} title="Upload de Planilha Excel (.xlsx)">
            <form onSubmit={handleUpload}>
                <div className="mb-4">
                    <label htmlFor="uploadDatasetName" className="block text-sm font-medium text-gray-300 mb-2">Nome do Conjunto de Dados</label>
                    <input id="uploadDatasetName" type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full input-style" placeholder="Ex: Importação de Maio" required />
                </div>
                <div className="mb-4">
                    <label htmlFor="fileUpload" className="block text-sm font-medium text-gray-300 mb-2">Arquivo (.xlsx)</label>
                    <input id="fileUpload" type="file" accept=".xlsx" onChange={handleFileChange} className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-500" required disabled={!xlsx} />
                    <p className="text-xs text-gray-400 mt-2">As colunas necessárias são: 'data', 'descrição', 'categoria', 'valor'.</p>
                </div>
                {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
                <div className="mt-6 flex justify-end gap-4">
                    <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-500 text-white font-semibold" disabled={isUploading}>Cancelar</button>
                    <button type="submit" className="px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center" disabled={isUploading || !file || !xlsx}>
                        {!xlsx && !error ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div> : null}
                        {isUploading ? 'Processando...' : (!xlsx && !error ? 'Carregando...' : 'Fazer Upload')}
                    </button>
                </div>
            </form>
        </Modal>
    );
}


// --- Componente: Dashboard ---
function Dashboard({ db, userId, datasetId, goBack }) {
    const [dataset, setDataset] = useState(null);
    const [allTransactions, setAllTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showTransactionModal, setShowTransactionModal] = useState(false);
    const [editingTransaction, setEditingTransaction] = useState(null);
    const [deletingTransaction, setDeletingTransaction] = useState(null);
    const [currentMonth, setCurrentMonth] = useState(new Date(2025, 6, 1)); // July 2025
    const [dashboardMode, setDashboardMode] = useState('normal');

    const datasetDocRef = useMemo(() => doc(db, 'artifacts', appId, 'public', 'data', 'datasets', datasetId), [db, datasetId]);

    useEffect(() => {
        const unsubscribe = onSnapshot(datasetDocRef, (doc) => {
            if (doc.exists()) {
                const data = doc.data();
                setDataset({ id: doc.id, ...data });
                setAllTransactions(data.transactions || []);
            } else {
                goBack();
            }
            setLoading(false);
        }, (error) => {
            console.error("Erro ao buscar dataset:", error);
            setLoading(false);
        });
        return () => unsubscribe();
    }, [datasetDocRef, goBack]);
    
    const transactionsForSelectedMonth = useMemo(() => {
        const start = startOfMonth(currentMonth);
        const end = endOfMonth(currentMonth);
        const monthlyTransactions = [];

        allTransactions.forEach(t => {
            if (t.isFixed) {
                const templateStartDate = parseISO(t.date);
                if (start >= startOfMonth(templateStartDate)) {
                    const dayOfMonth = templateStartDate.getDate();
                    let virtualDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), dayOfMonth);
                    if (virtualDate.getMonth() !== currentMonth.getMonth()) {
                        virtualDate = endOfMonth(currentMonth);
                    }
                    monthlyTransactions.push({
                        ...t,
                        originalId: t.id,
                        id: `${t.id}-${format(currentMonth, 'yyyy-MM')}`,
                        date: format(virtualDate, 'yyyy-MM-dd'),
                        status: 'Fixa',
                    });
                }
            } else if (t.repetitionInfo) {
                const tDate = parseISO(t.date);
                if (tDate >= start && tDate <= end) {
                    monthlyTransactions.push({
                        ...t,
                        status: `Repetição ${t.repetitionInfo.current} de ${t.repetitionInfo.total}`,
                    });
                }
            } else {
                const tDate = parseISO(t.date);
                if (tDate >= start && tDate <= end) {
                    monthlyTransactions.push(t);
                }
            }
        });

        return monthlyTransactions.sort((a, b) => new Date(b.date) - new Date(a.date));
    }, [allTransactions, currentMonth]);

    const handleUpsertTransaction = async (transactionData, repeatOptions) => {
        const { shouldRepeat, frequency, times } = repeatOptions;
        let finalTransactions = [...allTransactions];

        if (transactionData.id && !transactionData.originalId) {
             finalTransactions = finalTransactions.map(t =>
                t.id === transactionData.id ? transactionData : t
            );
        } else if (shouldRepeat) {
            const baseDate = parseISO(transactionData.date);
            const newTransactions = [];
            const repetitionGroupId = Date.now().toString();
            for (let i = 0; i < times; i++) {
                let nextDate;
                switch (frequency) {
                    case 'dias': nextDate = addDays(baseDate, i); break;
                    case 'semanas': nextDate = addWeeks(baseDate, i); break;
                    case 'meses': nextDate = addMonths(baseDate, i); break;
                    case 'anos': nextDate = addYears(baseDate, i); break;
                    default: nextDate = addMonths(baseDate, i);
                }
                newTransactions.push({
                    ...transactionData,
                    id: `${repetitionGroupId}-${i}`,
                    date: format(nextDate, 'yyyy-MM-dd'),
                    isFixed: false,
                    repetitionInfo: { current: i + 1, total: times, groupId: repetitionGroupId },
                });
            }
            finalTransactions = [...newTransactions, ...finalTransactions];
        } else {
            finalTransactions.unshift({
                ...transactionData,
                id: Date.now().toString(),
            });
        }

        try {
            await updateDoc(datasetDocRef, { transactions: finalTransactions });
            setShowTransactionModal(false);
            setEditingTransaction(null);
        } catch (error) {
            console.error("Erro ao salvar transação:", error);
        }
    };

    const executeDelete = async () => {
        if (!deletingTransaction) return;
    
        const idToDelete = deletingTransaction.originalId || deletingTransaction.id;
        let updatedTransactions;
    
        if (deletingTransaction.repetitionInfo) {
            const { groupId, current } = deletingTransaction.repetitionInfo;
            updatedTransactions = allTransactions.filter(t => {
                if (!t.repetitionInfo || t.repetitionInfo.groupId !== groupId) {
                    return true;
                }
                return t.repetitionInfo.current < current;
            });
        } else {
            updatedTransactions = allTransactions.filter(t => t.id !== idToDelete);
        }
    
        try {
            await updateDoc(datasetDocRef, { transactions: updatedTransactions });
        } catch (error) {
            console.error("Erro ao excluir transação:", error);
        } finally {
            setDeletingTransaction(null);
        }
    };

    const openEditModal = (transaction) => {
        const idToFind = transaction.originalId || transaction.id;
        const originalTransaction = allTransactions.find(t => t.id === idToFind);
        if (originalTransaction) {
            setEditingTransaction(originalTransaction);
            setShowTransactionModal(true);
        }
    };
    
    const openAddModal = () => {
        setEditingTransaction(null);
        setShowTransactionModal(true);
    };

    const handlePreviousMonth = () => setCurrentMonth(prev => subMonths(prev, 1));
    const handleNextMonth = () => setCurrentMonth(prev => addMonths(prev, 1));

    if (loading) {
        return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Carregando painel...</div>;
    }

    return (
        <div className="bg-gray-900 min-h-screen text-white">
            <header className="bg-gray-800 shadow-md p-4 flex items-center justify-between">
                <div className="flex items-center">
                    <button onClick={goBack} className="mr-4 p-2 rounded-full hover:bg-gray-700"><ArrowLeft className="h-6 w-6" /></button>
                    <h1 className="text-xl sm:text-2xl font-bold text-emerald-400">{dataset?.name}</h1>
                </div>
                <button onClick={openAddModal} className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-md flex items-center gap-2">
                    <PlusCircle className="h-5 w-5" />
                    <span className="hidden sm:inline">Nova Transação</span>
                </button>
            </header>

            <main className="p-4 sm:p-6 lg:p-8">
                <div className="flex items-center justify-center gap-4 mb-6 bg-gray-800 p-3 rounded-lg">
                    <button onClick={handlePreviousMonth} className="p-2 rounded-full hover:bg-gray-700"><ChevronLeft className="h-6 w-6" /></button>
                    <h2 className="text-xl font-semibold w-48 text-center capitalize">{format(currentMonth, "LLLL 'de' yyyy", { locale: ptBR })}</h2>
                    <button onClick={handleNextMonth} className="p-2 rounded-full hover:bg-gray-700"><ChevronRight className="h-6 w-6" /></button>
                </div>
                
                <div className="mb-6 bg-gray-800 p-4 rounded-lg">
                    <label htmlFor="dashboard-mode" className="text-sm text-gray-400 mr-2">Modo de Visualização:</label>
                    <select id="dashboard-mode" value={dashboardMode} onChange={e => setDashboardMode(e.target.value)} className="bg-gray-700 border-gray-600 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500">
                        <option value="normal">Dashboard Padrão</option>
                        <option value="limites">Controle de Limites</option>
                    </select>
                </div>

                {dashboardMode === 'normal' ? 
                    <SummaryCards transactions={transactionsForSelectedMonth} /> : 
                    <LimitsCards transactions={transactionsForSelectedMonth} />
                }

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <ExpensesByCategoryChart transactions={transactionsForSelectedMonth} />
                    <IncomeVsExpenseChart transactions={transactionsForSelectedMonth} />
                </div>
                
                <TransactionsTable transactions={transactionsForSelectedMonth} onEdit={openEditModal} onDelete={setDeletingTransaction} />
            </main>

            {showTransactionModal && <TransactionModal onClose={() => setShowTransactionModal(false)} onSave={handleUpsertTransaction} transaction={editingTransaction} />}
            {deletingTransaction && <ConfirmationModal transaction={deletingTransaction} onConfirm={executeDelete} onCancel={() => setDeletingTransaction(null)} />}
        </div>
    );
}

// --- Componentes do Dashboard ---

function SummaryCards({ transactions }) {
    const { income, expense, balance } = useMemo(() => {
        const income = transactions.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
        const expense = transactions.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);
        return { income, expense, balance: income - expense };
    }, [transactions]);

    const formatCurrency = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg"><h3 className="text-gray-400 text-sm font-medium">Receitas do Mês</h3><p className="text-2xl font-semibold text-green-400">{formatCurrency(income)}</p></div>
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg"><h3 className="text-gray-400 text-sm font-medium">Despesas do Mês</h3><p className="text-2xl font-semibold text-red-400">{formatCurrency(expense)}</p></div>
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg"><h3 className="text-gray-400 text-sm font-medium">Saldo do Mês</h3><p className={`text-2xl font-semibold ${balance >= 0 ? 'text-blue-400' : 'text-orange-400'}`}>{formatCurrency(balance)}</p></div>
        </div>
    );
}

function LimitsCards({ transactions }) {
    const limits = {
        essenciais: { value: 3340.00, categories: ['Essencial', 'Débito Essencial', 'Compra do mês'] },
        lazer: { value: 1737.74, categories: ['Lazer', 'Débito Lazer'] }
    };

    const limitsData = useMemo(() => {
        const essenciaisSpent = transactions.filter(t => t.type === 'expense' && limits.essenciais.categories.includes(t.category)).reduce((sum, r) => sum + r.amount, 0);
        const lazerSpent = transactions.filter(t => t.type === 'expense' && limits.lazer.categories.includes(t.category)).reduce((sum, r) => sum + r.amount, 0);
        return {
            essenciais: { spent: essenciaisSpent, limit: limits.essenciais.value, percentage: (essenciaisSpent / limits.essenciais.value) * 100, remaining: limits.essenciais.value - essenciaisSpent },
            lazer: { spent: lazerSpent, limit: limits.lazer.value, percentage: (lazerSpent / limits.lazer.value) * 100, remaining: limits.lazer.value - lazerSpent }
        };
    }, [transactions]);

    const formatCurrency = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    
    const LimitCard = ({ title, data, colorClass }) => (
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
            <p className={`text-2xl font-semibold ${data.percentage > 100 ? 'text-red-400' : colorClass}`}>{formatCurrency(data.spent)}</p>
            <p className="text-sm text-gray-500 mt-1">de {formatCurrency(data.limit)}</p>
            <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2"><div className={`${data.percentage > 100 ? 'bg-red-500' : 'bg-emerald-500'} h-2.5 rounded-full`} style={{ width: `${Math.min(data.percentage, 100)}%` }}></div></div>
            <p className="text-xs mt-1 text-gray-400">{data.remaining >= 0 ? `Restam ${formatCurrency(data.remaining)}` : `Excedeu ${formatCurrency(Math.abs(data.remaining))}`}</p>
        </div>
    );

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <LimitCard title="Essenciais e Compras" data={limitsData.essenciais} colorClass="text-orange-400" />
            <LimitCard title="Lazer" data={limitsData.lazer} colorClass="text-purple-400" />
        </div>
    );
}


function ExpensesByCategoryChart({ transactions }) {
    const data = useMemo(() => {
        const expenses = transactions.filter(t => t.type === 'expense');
        const grouped = expenses.reduce((acc, t) => {
            acc[t.category] = (acc[t.category] || 0) + t.amount;
            return acc;
        }, {});
        return Object.entries(grouped).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
    }, [transactions]);

    return (
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
            <h3 className="font-semibold mb-4">Gastos por Categoria (Mês)</h3>
            {data.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 80, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#4a5568" />
                        <XAxis type="number" stroke="#a0aec0" tickFormatter={(value) => `R$${value / 1000}k`} />
                        <YAxis type="category" dataKey="name" stroke="#a0aec0" width={80} tick={{ fontSize: 12 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#2d3748', border: 'none', borderRadius: '0.5rem' }} labelStyle={{ color: '#e2e8f0' }} formatter={(value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)} />
                        <Bar dataKey="value" fill="#ef4444" barSize={20} />
                    </BarChart>
                </ResponsiveContainer>
            ) : <p className="text-center text-gray-500 pt-16">Sem despesas para exibir neste mês.</p>}
        </div>
    );
}

function IncomeVsExpenseChart({ transactions }) {
    const data = useMemo(() => {
        const grouped = transactions.reduce((acc, t) => {
            const day = format(parseISO(t.date), 'dd/MM');
            if (!acc[day]) acc[day] = { name: day, income: 0, expense: 0 };
            if (t.type === 'income') acc[day].income += t.amount;
            else acc[day].expense += t.amount;
            return acc;
        }, {});
        return Object.values(grouped).sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
    }, [transactions]);

    return (
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
            <h3 className="font-semibold mb-4">Evolução Diária (Mês)</h3>
            {data.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#4a5568" />
                        <XAxis dataKey="name" stroke="#a0aec0" />
                        <YAxis stroke="#a0aec0" tickFormatter={(value) => `R$${value / 1000}k`} />
                        <Tooltip contentStyle={{ backgroundColor: '#2d3748', border: 'none', borderRadius: '0.5rem' }} labelStyle={{ color: '#e2e8f0' }} formatter={(value, name) => [new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value), name === 'income' ? 'Receita' : 'Despesa']} />
                        <Legend wrapperStyle={{ color: '#a0aec0' }} formatter={(value) => value === 'income' ? 'Receitas' : 'Despesas'} />
                        <Area type="monotone" dataKey="income" stroke="#4ade80" fill="#4ade80" fillOpacity={0.3} />
                        <Area type="monotone" dataKey="expense" stroke="#f87171" fill="#f87171" fillOpacity={0.3} />
                    </AreaChart>
                </ResponsiveContainer>
            ) : <p className="text-center text-gray-500 pt-16">Sem transações para exibir neste mês.</p>}
        </div>
    );
}

function TransactionsTable({ transactions, onEdit, onDelete }) {
    const formatCurrency = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    const formatDate = (dateString) => format(parseISO(dateString), 'dd/MM/yyyy');

    return (
        <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
            <h3 className="font-semibold mb-4">Transações do Mês</h3>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-gray-700"><th className="p-3">Data</th><th className="p-3">O que é</th><th className="p-3">Cartão</th><th className="p-3">Categoria</th><th className="p-3">Status</th><th className="p-3 text-right">Valor</th><th className="p-3 text-center">Ações</th></tr>
                    </thead>
                    <tbody>
                        {transactions.length > 0 ? transactions.map(t => (
                            <tr key={t.id} className="border-b border-gray-700 hover:bg-gray-700/50">
                                <td className="p-3">{formatDate(t.date)}</td>
                                <td className="p-3">{t.description}</td>
                                <td className="p-3">{t.card}</td>
                                <td className="p-3"><span className="bg-gray-600 px-2 py-1 rounded-full text-xs font-medium">{t.category}</span></td>
                                <td className="p-3 text-sm">
                                    {t.status && <span className={`px-2 py-1 rounded-full text-xs font-medium ${t.isFixed ? 'bg-blue-600' : 'bg-purple-600'}`}>{t.status}</span>}
                                </td>
                                <td className={`p-3 text-right font-medium ${t.type === 'income' ? 'text-green-400' : 'text-red-400'}`}>{t.type === 'expense' && '- '}{formatCurrency(t.amount)}</td>
                                <td className="p-3 text-center"><button onClick={() => onEdit(t)} className="p-1 text-gray-400 hover:text-blue-400 mr-2"><Edit className="h-5 w-5" /></button><button onClick={() => onDelete(t)} className="p-1 text-gray-400 hover:text-red-400"><Trash2 className="h-5 w-5" /></button></td>
                            </tr>
                        )) : (
                            <tr><td colSpan="7" className="text-center text-gray-500 py-8">Nenhuma transação encontrada para este mês.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// --- Componente Modal Genérico e Modal de Transação ---

function Modal({ onClose, children, title, subTitle }) {
    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-lg text-white">
                <div className="flex justify-between items-start p-5 border-b border-gray-700">
                    <div>
                        <h3 className="text-xl font-semibold">{title}</h3>
                        {subTitle && <p className="text-sm text-gray-400 mt-1">{subTitle}</p>}
                    </div>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-700 -mt-1 -mr-1"><X className="h-6 w-6" /></button>
                </div>
                <div className="p-6">{children}</div>
            </div>
        </div>
    );
}

function ConfirmationModal({ transaction, onConfirm, onCancel }) {
    let alertMessage = 'Tem certeza que deseja excluir esta transação?';
    if (transaction.isFixed) {
        alertMessage = 'Você tem certeza? Isto irá remover a despesa fixa de todos os meses futuros.';
    } else if (transaction.repetitionInfo) {
        alertMessage = 'Esta é uma transação repetida. Deseja excluir esta e todas as parcelas futuras?';
    }

    return (
        <Modal onClose={onCancel} title="Confirmar Exclusão">
            <p className="text-gray-300 mb-6">{alertMessage}</p>
            <div className="flex justify-end gap-4">
                <button onClick={onCancel} className="px-4 py-2 rounded-md bg-gray-600 hover:bg-gray-500 text-white font-semibold">Cancelar</button>
                <button onClick={onConfirm} className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-500 text-white font-semibold">Excluir</button>
            </div>
        </Modal>
    );
}


function ToggleSwitch({ label, description, checked, onChange, disabled }) {
    return (
        <div className="flex items-center justify-between py-2">
            <div>
                <label htmlFor={label} className="text-sm font-medium text-white">{label}</label>
                <p className="text-sm text-gray-400">{description}</p>
            </div>
            <label htmlFor={label} className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id={label} className="sr-only peer" checked={checked} onChange={e => onChange(e.target.checked)} disabled={disabled} />
                <div className="w-11 h-6 bg-gray-600 rounded-full peer peer-focus:ring-2 peer-focus:ring-blue-500 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
        </div>
    );
}

function CurrencyInput({ value, onChange }) {
    const [displayValue, setDisplayValue] = useState('0,00');

    useEffect(() => {
        const formatted = new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
        }).format(value || 0);
        setDisplayValue(formatted);
    }, [value]);

    const handleChange = (e) => {
        let inputVal = e.target.value.replace(/\D/g, '');
        if (inputVal === '') {
            onChange(0);
            return;
        }
        const numericValue = Number(inputVal) / 100;
        onChange(numericValue);
    };

    return (
        <input
            type="text"
            value={displayValue}
            onChange={handleChange}
            className="w-full input-style text-right"
            placeholder="0,00"
        />
    );
}

function TransactionModal({ onClose, onSave, transaction }) {
    const [formData, setFormData] = useState({
        id: transaction?.id || null, 
        description: transaction?.description || '', 
        amount: transaction?.amount || 0, 
        category: transaction?.category || '', 
        date: transaction?.date || format(new Date(), 'yyyy-MM-dd'), 
        type: transaction?.type || 'expense', 
        isFixed: transaction?.isFixed || false,
        card: transaction?.card || '',
    });
    const [showMoreDetails, setShowMoreDetails] = useState(transaction?.isFixed || (transaction?.repetitionInfo && !transaction.isFixed));
    const [shouldRepeat, setShouldRepeat] = useState(false);
    const [repeatFrequency, setRepeatFrequency] = useState('meses');
    const [repeatTimes, setRepeatTimes] = useState(2);

    const cardOptions = ['C6', 'Nubank Yara', 'Nubank Gab', 'Picpay', 'Wise', 'Payoneer', 'Inter'];
    const predefinedCategories = ['Essencial', 'Lazer', 'Investimento', 'Viagem', 'Doação', 'Débito Essencial', 'Débito Lazer', 'Compra do mês'];

    const handleChange = (e) => setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    const handleAmountChange = (newValue) => setFormData(prev => ({ ...prev, amount: newValue }));
    const handleFixedToggle = (checked) => {
        setFormData(p => ({ ...p, isFixed: checked }));
        if (checked) setShouldRepeat(false);
    };
    const handleRepeatToggle = (checked) => {
        setShouldRepeat(checked);
        if (checked) setFormData(p => ({ ...p, isFixed: false }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave({ ...formData }, { shouldRepeat, frequency: repeatFrequency, times: repeatTimes });
    };

    return (
        <Modal onClose={onClose} title="Adicionar Nova Transação" subTitle="Adicione uma nova receita ou despesa ao seu projeto">
            <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div><label htmlFor="date" className="block text-sm font-medium text-gray-300 mb-1">Data</label><input type="date" name="date" value={formData.date} onChange={handleChange} className="w-full input-style" required /></div>
                    <div><label htmlFor="type" className="block text-sm font-medium text-gray-300 mb-1">Tipo</label><select name="type" value={formData.type} onChange={handleChange} className="w-full input-style" required><option value="expense">Despesa</option><option value="income">Receita</option></select></div>
                    <div><label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">O que é</label><input type="text" name="description" placeholder="Ex: Salário, Supermercado..." value={formData.description} onChange={handleChange} className="w-full input-style" required /></div>
                    <div><label htmlFor="card" className="block text-sm font-medium text-gray-300 mb-1">Cartão</label><select name="card" value={formData.card} onChange={handleChange} className="w-full input-style" required><option value="" disabled>Selecione um cartão</option>{cardOptions.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
                    <div><label htmlFor="amount" className="block text-sm font-medium text-gray-300 mb-1">Valor</label><CurrencyInput value={formData.amount} onChange={handleAmountChange} /></div>
                    <div><label htmlFor="category" className="block text-sm font-medium text-gray-300 mb-1">Categoria</label><select name="category" value={formData.category} onChange={handleChange} className="w-full input-style" required><option value="" disabled>Selecione uma categoria</option>{predefinedCategories.map(cat => <option key={cat} value={cat}>{cat}</option>)}</select></div>
                </div>
                
                <button type="button" onClick={() => setShowMoreDetails(!showMoreDetails)} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white py-2">{showMoreDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />} Mais detalhes</button>
                
                {showMoreDetails && (
                    <div className="space-y-2 pt-4 mt-2 border-t border-gray-700">
                        <ToggleSwitch label="Despesa fixa" description="Transação se repete automaticamente" checked={formData.isFixed} onChange={handleFixedToggle} disabled={!!transaction?.repetitionInfo} />
                        <div className="border-t border-gray-700"></div>
                        <ToggleSwitch label="Repetir transação" description="Definir frequência e número de repetições" checked={shouldRepeat} onChange={handleRepeatToggle} disabled={!!transaction || formData.isFixed} />
                        
                        {shouldRepeat && !transaction && (
                            <div className="grid grid-cols-2 gap-4 pl-4 border-l-2 border-gray-600 ml-2 pt-2">
                                <div><label htmlFor="repeatFrequency" className="text-sm">Frequência</label><select id="repeatFrequency" value={repeatFrequency} onChange={e => setRepeatFrequency(e.target.value)} className="w-full input-style mt-1"><option value="dias">Dias</option><option value="semanas">Semanas</option><option value="meses">Meses</option><option value="anos">Anos</option></select></div>
                                <div><label htmlFor="repeatTimes" className="text-sm">Vezes</label><input id="repeatTimes" type="number" min={2} value={repeatTimes} onChange={e => setRepeatTimes(Math.max(2, parseInt(e.target.value) || 2))} className="w-full input-style mt-1" /></div>
                            </div>
                        )}
                    </div>
                )}

                <div className="mt-6 flex justify-end gap-4"><button type="button" onClick={onClose} className="px-6 py-2 rounded-md bg-gray-600 hover:bg-gray-500 text-white font-semibold">Cancelar</button><button type="submit" className="px-6 py-2 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-semibold">Adicionar</button></div>
            </form>
        </Modal>
    );
}

// Estilos reutilizáveis para inputs
const tailwindStyles = `.input-style { background-color: #374151; border: 1px solid #4B5563; border-radius: 0.375rem; padding: 0.5rem 0.75rem; color: white; } .input-style:focus { --tw-ring-color: #3b82f6; border-color: #3b82f6; outline: 2px solid transparent; outline-offset: 2px; box-shadow: var(--tw-ring-inset) 0 0 0 calc(1px + var(--tw-ring-offset-width)) var(--tw-ring-color); }`;
const styleSheet = document.createElement("style");
styleSheet.innerText = tailwindStyles;
document.head.appendChild(styleSheet);