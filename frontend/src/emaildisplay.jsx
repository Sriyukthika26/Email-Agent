import React from 'react';
import { ArrowLeft, ArrowRight, Edit, Check, Send, RefreshCw, ThumbsUp, ThumbsDown } from 'lucide-react';
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
    handleApprove,
    satisfactionChoice,
    setSatisfactionChoice
}) => {
    const currentEmail = historyIndex >= 0 ? emailHistory[historyIndex] : null;
    const [showRegenerateInput, setShowRegenerateInput] = React.useState(false);

    // Reset local state when navigating history
    React.useEffect(() => {
        setSatisfactionChoice(null);
        setShowRegenerateInput(false);
    }, [historyIndex, setSatisfactionChoice]);


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
                <div className="mt-4 space-y-4 pt-4 border-t">
                    {/* Step 1: Initial Satisfaction Check (Show if not editing and no choice made) */}
                    {!isEditing && satisfactionChoice === null && (
                        <div className="p-4 text-center bg-gray-50 rounded-lg">
                            <h3 className="font-semibold mb-3 text-gray-800">Are you satisfied with this draft?</h3>
                            <div className="flex justify-center items-center space-x-4">
                                <IconButton onClick={() => setSatisfactionChoice('unsatisfied')} className="text-red-500 hover:bg-red-100" title="Unsatisfied">
                                    <ThumbsDown size={24} />
                                </IconButton>
                                <IconButton onClick={() => setSatisfactionChoice('satisfied')} className="text-green-500 hover:bg-green-100" title="Satisfied">
                                    <ThumbsUp size={24} />
                                </IconButton>
                            </div>
                        </div>
                    )}

                    {/* Step 2 (Thumbs Down): Show correction options */}
                    {!isEditing && satisfactionChoice === 'unsatisfied' && (
                        <div className="p-4 text-center bg-gray-50 rounded-lg space-y-4">
                             <h3 className="font-semibold text-gray-800">What needs to be changed?</h3>
                             <div className="flex justify-center items-center space-x-3">
                                <button onClick={() => { setSatisfactionChoice(null); setShowRegenerateInput(false); }} className="font-semibold text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                                    Back
                                </button>
                                <button onClick={() => setShowRegenerateInput(true)} className="font-semibold text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                                    Regenerate (for major changes)
                                </button>
                                <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-indigo-600 px-4 py-2 rounded-lg hover:bg-indigo-100 transition-colors">
                                    <Edit size={18} />
                                    Edit Manually (for minor fixes)
                                </button>
                             </div>
                             {showRegenerateInput && (
                                <div className="flex space-x-2 pt-3">
                                    <input type="text" value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="e.g., 'Make it more formal'" className="flex-grow px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
                                    <PrimaryButton onClick={handleRegenerateWithFeedback} disabled={!feedback || isRegenerating || isLoading} isLoading={isRegenerating} className="w-auto px-4">
                                        <RefreshCw size={16} />
                                    </PrimaryButton>
                                </div>
                             )}
                        </div>
                    )}

                    {/* Step 2 (Thumbs Up): Show finalization options */}
                    {!isEditing && satisfactionChoice === 'satisfied' && (
                        <div className="flex items-center justify-end space-x-3">
                             <button onClick={() => setSatisfactionChoice(null)} className="font-semibold text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                                Back
                            </button>
                            <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors">
                                <Edit size={18} />
                                Edit
                            </button>
                            <PrimaryButton onClick={handleApprove} disabled={isLoading} isLoading={isLoading && !!currentEmail} className="bg-green-600 hover:bg-green-700 focus:ring-green-500">
                                <Send size={16} className="mr-2" />
                                Approve & Send
                            </PrimaryButton>
                        </div>
                    )}

                    {/* Actions shown ONLY when editing */}
                    {isEditing && (
                        <div className="flex items-center justify-end">
                             <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-indigo-600 px-4 py-2 rounded-lg hover:bg-indigo-100 transition-colors">
                                <Check size={18} />
                                Save & Continue
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default EmailDisplay;
