import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, ArrowRight, Edit, Check, Send, RefreshCw } from 'lucide-react';

// --- API Client ---
// This now points to the live Python backend
// const API_BASE_URL = 'https://email-agent-backend-4oxl.onrender.com';

const API_BASE_URL = 'http://localhost:8000';

const api = {
    generateEmail: async (leadId, userId, userInstructions) => {
        const response = await fetch(`${API_BASE_URL}/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ leadId, userId, user_instructions: userInstructions }),  
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to generate email');
    }
    return response.json();
  },
  // This single function now handles both regeneration and approval
  updateEmail: async (thread_id, decision, feedback = null) => {
    const response = await fetch(`${API_BASE_URL}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id, decision, feedback })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update email');
    }
    return response.json();
  }
};


// --- UI Components ---

const InputField = ({ id, label, value, onChange }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <input
            type="text"
            id={id}
            value={value}
            onChange={onChange}
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-shadow"
        />
    </div>
);

const TextareaField = ({ id, label, value, onChange, placeholder }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
        <textarea
            id={id}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            rows="3"
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-shadow"
        />
    </div>
);
const IconButton = ({ onClick, children, disabled = false, className = '' }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        className={`p-2 rounded-full hover:bg-gray-200 disabled:bg-transparent disabled:text-gray-300 disabled:cursor-not-allowed transition-colors ${className}`}
    >
        {children}
    </button>
);

const PrimaryButton = ({ onClick, children, disabled = false, isLoading = false, className = '', title = '' }) => (
    <button
        onClick={onClick}
        disabled={disabled || isLoading}
        title={title}
        className={`w-full flex justify-center items-center bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out disabled:bg-indigo-300 disabled:cursor-not-allowed ${className}`}
    >
        {isLoading ? <RefreshCw className="animate-spin h-5 w-5" /> : children}
    </button>
);

const DataCard = ({ title, data }) => (
    <details className="bg-gray-50 p-3 rounded-lg border border-gray-200">
        <summary className="font-semibold text-gray-800 cursor-pointer">{title}</summary>
        <div className="mt-2 text-xs text-gray-600">
            <pre className="bg-gray-100 p-2 rounded whitespace-pre-wrap break-all">{JSON.stringify(data, null, 2)}</pre>
        </div>
    </details>
);

// --- Main App Component ---

export default function App() {
    const [leadId, setLeadId] = useState('2094');
    const [userId, setUserId] = useState('53');
    const [userInstructions, setUserInstructions] = useState(''); 
    const [retrievedData, setRetrievedData] = useState(null);
    const [emailHistory, setEmailHistory] = useState([]);
    const [historyIndex, setHistoryIndex] = useState(-1);
    const [currentThreadId, setCurrentThreadId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isRegenerating, setIsRegenerating] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editedEmail, setEditedEmail] = useState({ subject: '', body: '' });
    const [feedback, setFeedback] = useState('');
    const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });

    const currentEmail = historyIndex >= 0 ? emailHistory[historyIndex] : null;

    useEffect(() => {
        if (notification.show) {
            const timer = setTimeout(() => setNotification({ show: false, message: '', type: 'success' }), 3000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

    const showNotification = (message, type = 'error') => {
        setNotification({ show: true, message, type });
    };
    
    const handleGenerate = useCallback(async () => {
        setIsLoading(true);
        // Reset previous results for a new generation
        setEmailHistory([]);
        setHistoryIndex(-1);
        setRetrievedData(null);
        setCurrentThreadId(null);

        try {
            const result = await api.generateEmail(leadId, userId, userInstructions);
            
            setRetrievedData(result.retrievedData);
            setCurrentThreadId(result.thread_id);
            setEmailHistory([result.email]);
            setHistoryIndex(0);
            
        } catch (error) {
            console.error("Error generating email:", error);
            showNotification(error.message || 'An unknown error occurred.');
        } finally {
            setIsLoading(false);
        }
    }, [leadId, userId, userInstructions]);

    const handleRegenerateWithFeedback = async () => {
        if (!currentThreadId || !feedback) return;
        setIsRegenerating(true);
        try {
            const result = await api.updateEmail(currentThreadId, 'regenerate', feedback);
            if (result.email) {
                const newHistory = [...emailHistory, result.email];
                setEmailHistory(newHistory);
                setHistoryIndex(newHistory.length - 1);
                setFeedback(''); // Clear feedback input after use
                showNotification(result.message, 'info');
            }
        } catch (error) {
            showNotification(error.message);
        } finally {
            setIsRegenerating(false);
        }
    };

    const handleApprove = async () => {
        if (!currentThreadId) return;
        setIsLoading(true);
        try {
            const result = await api.updateEmail(currentThreadId, 'approve');
            showNotification(result.message, 'success');
            // Reset state after approval
            setEmailHistory([]);
            setHistoryIndex(-1);
            setRetrievedData(null);
            setCurrentThreadId(null);
        } catch (error) {
            showNotification(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEditToggle = () => {
        if (!currentEmail) return;
        if (isEditing) {
            const newHistory = emailHistory.slice(0, historyIndex + 1);
            newHistory.push(editedEmail);
            setEmailHistory(newHistory);
            setHistoryIndex(newHistory.length - 1);
        } else {
            setEditedEmail(currentEmail);
        }
        setIsEditing(!isEditing);
    };

    const navigateHistory = (direction) => {
        setIsEditing(false);
        setHistoryIndex(prev => Math.max(0, Math.min(emailHistory.length - 1, prev + direction)));
    };

    return (
        <div className="bg-gray-100 min-h-screen font-sans text-gray-800">
            <div className="container mx-auto p-4 md:p-8 max-w-6xl">
                <header className="bg-white shadow-lg rounded-xl p-6 mb-8 border border-gray-200">
                    <h1 className="text-3xl font-bold text-gray-900">AI Email Agent</h1>
                    <p className="text-gray-600 mt-1">React Frontend with Live Python Backend</p>
                </header>

                <main className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    <div className="lg:col-span-2 bg-white p-6 shadow-lg rounded-xl border border-gray-200 h-fit">
                        <h2 className="text-xl font-semibold mb-4 border-b pb-3">Controls</h2>
                        <div className="space-y-4">
                            <InputField id="leadId" label="Lead ID" value={leadId} onChange={(e) => setLeadId(e.target.value)} />
                            <InputField id="userId" label="User ID" value={userId} onChange={(e) => setUserId(e.target.value)} />
                            <TextareaField 
                                id="userInstructions"
                                label="Optional Instructions / Tone"
                                value={userInstructions}
                                onChange={(e) => setUserInstructions(e.target.value)}
                                placeholder="e.g., 'Be very formal and direct.' or 'Mention that we are offering a 10% discount this month.'"
                            />
                            <PrimaryButton onClick={handleGenerate} disabled={isLoading} isLoading={isLoading && !currentEmail}>
                                Generate Email
                            </PrimaryButton>
                        </div>

                        {retrievedData && (
                        <div className="mt-6 space-y-3">
                            <h3 className="font-semibold text-lg">Retrieved Data</h3>
                            <DataCard title="Lead Info (crm_lead)" data={retrievedData.crm_lead} />
                            <DataCard title="Stage Info (crm_stage)" data={retrievedData.crm_stage} />
                            <DataCard title="User Info (res_users)" data={retrievedData.res_users} />
                            <DataCard title="User Contact (res_partner)" data={retrievedData.res_partner} />
                            <DataCard title="Company Info (organization)" data={retrievedData.organization} />
                        </div>
                        )}
                    </div>

                    <div className="lg:col-span-3 bg-white p-6 shadow-lg rounded-xl border border-gray-200">
                        <div className="flex justify-between items-center mb-4 border-b pb-3">
                            <h2 className="text-xl font-semibold">Generated Email</h2>
                            {emailHistory.length > 0 && (
                                <div className="flex items-center space-x-2">
                                    <IconButton onClick={() => navigateHistory(-1)} disabled={historyIndex <= 0}>
                                        <ArrowLeft size={20} />
                                    </IconButton>
                                    <span className="text-sm font-medium text-gray-600 tabular-nums">
                                        {historyIndex + 1} / {emailHistory.length}
                                    </span>
                                    <IconButton onClick={() => navigateHistory(1)} disabled={historyIndex >= emailHistory.length - 1}>
                                        <ArrowRight size={20} />
                                    </IconButton>
                                </div>
                            )}
                        </div>

                        <div className="min-h-[400px] border rounded-lg bg-gray-50 p-4 flex flex-col">
                            {isLoading && !currentEmail ? (
                                <div className="flex-grow flex items-center justify-center">
                                    <RefreshCw className="h-10 w-10 text-indigo-500 animate-spin" />
                                </div>
                            ) : currentEmail ? (
                                <div className="flex-grow flex flex-col">
                                    {isEditing ? (
                                        <>
                                            <input type="text" value={editedEmail.subject} onChange={(e) => setEditedEmail({...editedEmail, subject: e.target.value})} className="text-lg font-semibold bg-white border border-indigo-300 rounded p-2 mb-4 focus:ring-2 focus:ring-indigo-500 outline-none" />
                                            <textarea value={editedEmail.body} onChange={(e) => setEditedEmail({...editedEmail, body: e.target.value})} className="flex-grow text-gray-700 bg-white border border-indigo-300 rounded p-2 leading-relaxed whitespace-pre-wrap focus:ring-2 focus:ring-indigo-500 outline-none" rows="12" />
                                        </>
                                    ) : (
                                        <>
                                            <h3 className="text-lg font-semibold mb-4 pb-2 border-b">{currentEmail.subject}</h3>
                                            <p className="flex-grow text-gray-700 leading-relaxed whitespace-pre-wrap">{currentEmail.body}</p>
                                        </>
                                    )}
                                </div>
                            ) : (
                                <div className="flex-grow flex items-center justify-center text-gray-500">
                                    Enter Lead and User IDs, then click "Generate Email" to start.
                                </div>
                            )}
                        </div>
                        
                        {currentEmail && (
                             <div className="mt-4 space-y-4">
                                <div className="space-y-2">
                                    <h3 className="font-semibold">Provide Feedback to Regenerate</h3>
                                    <div className="flex space-x-2">
                                        <input type="text" value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="e.g., 'Make it more formal'" className="flex-grow px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                        <PrimaryButton 
                                            onClick={handleRegenerateWithFeedback}
                                            disabled={!feedback || isRegenerating || isLoading}
                                            isLoading={isRegenerating}
                                            className="w-auto px-4"
                                        >
                                            <RefreshCw size={16} />
                                        </PrimaryButton>
                                    </div>
                                </div>

                                <div className="flex items-center justify-end space-x-3 pt-4 border-t">
                                    <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors">
                                        {isEditing ? <Check size={18} /> : <Edit size={18} />}
                                        {isEditing ? 'Save Edit' : 'Edit Manually'}
                                    </button>
                                    <PrimaryButton onClick={handleApprove} disabled={isLoading} isLoading={isLoading && currentEmail} className="bg-green-600 hover:bg-green-700 focus:ring-green-500">
                                        <Send size={16} className="mr-2" />
                                        Approve & Send
                                    </PrimaryButton>
                                </div>
                            </div>
                        )}
                    </div>
                </main>
                
                {notification.show && (
                    <div className={`fixed bottom-5 right-5 p-4 rounded-lg shadow-xl text-white ${notification.type === 'success' ? 'bg-green-500' : notification.type === 'info' ? 'bg-blue-500' : 'bg-red-500'} transition-transform transform animate-bounce`}>
                        {notification.message}
                    </div>
                )}
            </div>
        </div>
    );
}
