import React from 'react';
import { ArrowLeft, ArrowRight, Edit, Check, Send, RefreshCw } from 'lucide-react';
import { IconButton, PrimaryButton } from './components';

const EmailDisplay = ({
    emailHistory,
    historyIndex,
    isLoading,
    isRegenerating,
    isEditing,
    editedEmail,
    setEditedEmail,
    feedback,
    setFeedback,
    navigateHistory,
    handleEditToggle,
    handleRegenerateWithFeedback,
    handleApprove
}) => {
    const currentEmail = historyIndex >= 0 ? emailHistory[historyIndex] : null;

    return (
        <div className="lg:col-span-3 bg-white p-6 shadow-lg rounded-xl border border-gray-200">
            {/* --- Header and History Navigation --- */}
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

            {/* --- Email Content Area --- */}
            <div className="min-h-[400px] border rounded-lg bg-gray-50 p-4 flex flex-col">
                {isLoading && !currentEmail ? (
                    <div className="flex-grow flex items-center justify-center">
                        <RefreshCw className="h-10 w-10 text-indigo-500 animate-spin" />
                    </div>
                ) : currentEmail ? (
                    <div className="flex-grow flex flex-col">
                        {isEditing ? (
                            <>
                                <input type="text" value={editedEmail.subject} onChange={(e) => setEditedEmail({ ...editedEmail, subject: e.target.value })} className="text-lg font-semibold bg-white border border-indigo-300 rounded p-2 mb-4 focus:ring-2 focus:ring-indigo-500 outline-none" />
                                <textarea value={editedEmail.body} onChange={(e) => setEditedEmail({ ...editedEmail, body: e.target.value })} className="flex-grow text-gray-700 bg-white border border-indigo-300 rounded p-2 leading-relaxed whitespace-pre-wrap focus:ring-2 focus:ring-indigo-500 outline-none" rows="12" />
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
                        Enter IDs and click "Generate Email" to start.
                    </div>
                )}
            </div>

            {/* --- Action Buttons Area --- */}
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
                        <PrimaryButton onClick={handleApprove} disabled={isLoading} isLoading={isLoading && !!currentEmail} className="bg-green-600 hover:bg-green-700 focus:ring-green-500">
                            <Send size={16} className="mr-2" />
                            Approve & Send
                        </PrimaryButton>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmailDisplay;
