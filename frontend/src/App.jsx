import React, { useState, useEffect, useCallback } from 'react';
import * as api from './api';
import { Notification } from './components';
import ControlPanel from './controlpanel';
import EmailDisplay from './emaildisplay';

export default function App() {
    // --- State Management ---
    const [leadId, setLeadId] = useState('25649');
    const [userId, setUserId] = useState('294');
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
    const [satisfactionChoice, setSatisfactionChoice] = useState(null);

    // Read leadId and userId from URL on initial load
    useEffect(() => {
        const queryParams = new URLSearchParams(window.location.search);
        const urlLeadId = queryParams.get('leadId');
        const urlUserId = queryParams.get('userId');

        if (urlLeadId) {
            setLeadId(urlLeadId);
        }
        if (urlUserId) {
            setUserId(urlUserId);
        }
    }, []); // The empty array ensures this runs only once on component mount

    // --- Notification Logic ---
    useEffect(() => {
        if (notification.show) {
            const timer = setTimeout(() => setNotification({ show: false, message: '', type: 'success' }), 3000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

    const showNotification = (message, type = 'error') => {
        setNotification({ show: true, message, type });
    };

    // --- API Handlers ---
    const handleGenerate = useCallback(async () => {
        setIsLoading(true);
        setEmailHistory([]);
        setHistoryIndex(-1);
        setRetrievedData(null);
        setCurrentThreadId(null);
        setSatisfactionChoice(null);

        try {
            const result = await api.generateEmail(leadId, userId, userInstructions);
            setRetrievedData(result.retrievedData);
            setCurrentThreadId(result.thread_id);
            setEmailHistory([result.email]);
            setHistoryIndex(0);
        } catch (error) {
            showNotification(error.message || 'An unknown error occurred.');
        } finally {
            setIsLoading(false);
        }
    }, [leadId, userId, userInstructions]);

    const handleRegenerateWithFeedback = async () => {
        if (!currentThreadId || !feedback) return;
        setIsRegenerating(true);
        setSatisfactionChoice(null);

        try {
            const result = await api.updateEmail(currentThreadId, 'regenerate', feedback, emailHistory);
            if (result.email) {
                const newHistoryFromServer = [...emailHistory, result.email];
                setEmailHistory(newHistoryFromServer);
                setHistoryIndex(newHistoryFromServer.length - 1);
                setFeedback('');
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
            // The latest history (including edits) is already on the backend,
            // so we don't need to send it again.
            const result = await api.updateEmail(currentThreadId, 'approve');
            showNotification(result.message, 'success');
            
            setEmailHistory([]);
            setHistoryIndex(-1);
            setRetrievedData(null);
            setCurrentThreadId(null);
            setSatisfactionChoice(null);
        } catch (error) {
            showNotification(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    // --- UI Handlers ---
    const handleEditToggle = async () => {
        const currentEmail = emailHistory[historyIndex];
        if (!currentEmail) return;

        if (isEditing) {
            const newHistory = [...emailHistory.slice(0, historyIndex + 1), editedEmail];
            setEmailHistory(newHistory);
            setHistoryIndex(newHistory.length - 1);
            setIsEditing(false);
            try {
                await api.updateHistory(currentThreadId, newHistory);
                showNotification("Edit saved to backend.", "info");
            } catch (error) {
                showNotification(`Failed to save edit: ${error.message}`, "error");
            }
        } else {
            setEditedEmail(currentEmail);
            setIsEditing(true);
        }
    };

    const navigateHistory = (direction) => {
        setIsEditing(false);
        setSatisfactionChoice(null);
        setHistoryIndex(prev => Math.max(0, Math.min(emailHistory.length - 1, prev + direction)));
    };

    // --- Render ---
    const queryParams = new URLSearchParams(window.location.search);
    const idsAreFromUrl = !!(queryParams.get('leadId') || queryParams.get('userId'));

    return (
        <div className="bg-[#f8fafc] min-h-screen font-sans text-[#111827]">
            <div className="container mx-auto p-4 md:p-8 max-w-6xl">
                <header className="bg-white shadow-lg rounded-xl p-6 mb-8 border border-[#e5e7eb]">
                    <h1 className="text-3xl font-bold text-[#111827]">AI Email Agent</h1>
                </header>

                <main className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    <ControlPanel
                        leadId={leadId}
                        setLeadId={setLeadId}
                        userId={userId}
                        setUserId={setUserId}
                        idsAreFromUrl={idsAreFromUrl}
                        userInstructions={userInstructions}
                        setUserInstructions={setUserInstructions}
                        handleGenerate={handleGenerate}
                        isLoading={isLoading}
                        currentEmail={emailHistory[historyIndex]}
                        retrievedData={retrievedData}
                    />
                    <EmailDisplay
                        emailHistory={emailHistory}
                        historyIndex={historyIndex}
                        isLoading={isLoading}
                        isRegenerating={isRegenerating}
                        isEditing={isEditing}
                        editedEmail={editedEmail}
                        setEditedEmail={setEditedEmail}
                        feedback={feedback}
                        setFeedback={setFeedback}
                        navigateHistory={navigateHistory}
                        handleEditToggle={handleEditToggle}
                        handleRegenerateWithFeedback={handleRegenerateWithFeedback}
                        handleApprove={handleApprove}
                        satisfactionChoice={satisfactionChoice}
                        setSatisfactionChoice={setSatisfactionChoice}
                    />
                </main>

                <Notification
                    show={notification.show}
                    message={notification.message}
                    type={notification.type}
                />
            </div>
        </div>
    );
}
