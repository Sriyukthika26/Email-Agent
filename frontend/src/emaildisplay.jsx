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

    React.useEffect(() => {
        setSatisfactionChoice(null);
        setShowRegenerateInput(false);
    }, [historyIndex, setSatisfactionChoice]);

    return (
        <div className="lg:col-span-3 bg-white p-6 shadow-lg rounded-xl border border-[#e5e7eb]">
            <div className="flex justify-between items-center mb-4 border-b border-[#e5e7eb] pb-3">
                <h2 className="text-xl font-semibold text-[#111827]">Generated Email</h2>
                {emailHistory.length > 0 && (
                    <div className="flex items-center space-x-2">
                        <IconButton onClick={() => navigateHistory(-1)} disabled={historyIndex <= 0}>
                        <ArrowLeft size={20} />
                        </IconButton>
                        <span className="text-sm font-medium text-[#6b7280] tabular-nums">
                            {historyIndex + 1} / {emailHistory.length}
                            </span>
                        <IconButton onClick={() => navigateHistory(1)} disabled={historyIndex >= emailHistory.length - 1}>
                            <ArrowRight size={20} />
                            </IconButton>
                    </div>
                )}
            </div>

            <div className="min-h-[400px] border border-[#e5e7eb] rounded-lg bg-[#f8fafc] p-4 flex flex-col">
                {isLoading && !currentEmail ? (
                    <div className="flex-grow flex items-center justify-center">
                        <RefreshCw className="h-10 w-10 text-[#16a34a] animate-spin" />
                        </div>
                ) : currentEmail ? (
                    <div className="flex-grow flex flex-col">
                        {isEditing ? (
                            <>
                                <input type="text" value={editedEmail.subject} onChange={(e) => setEditedEmail({ ...editedEmail, subject: e.target.value })} className="text-lg font-semibold bg-white border border-[#16a34a] rounded p-2 mb-4 focus:ring-2 focus:ring-[#16a34a] outline-none" />
                                <textarea value={editedEmail.body} onChange={(e) => setEditedEmail({ ...editedEmail, body: e.target.value })} className="flex-grow text-[#111827] bg-white border border-[#16a34a] rounded p-2 leading-relaxed whitespace-pre-wrap focus:ring-2 focus:ring-[#16a34a] outline-none" rows="12" />
                            </>
                        ) : (
                            <>
                                <h3 className="text-lg font-semibold mb-4 pb-2 border-b border-[#e5e7eb]">{currentEmail.subject}</h3>
                                <p className="flex-grow text-[#111827] leading-relaxed whitespace-pre-wrap">{currentEmail.body}</p>
                            </>
                        )}
                    </div>
                ) : (
                    <div className="flex-grow flex items-center justify-center text-[#6b7280]">click "Generate Email" to start.</div>
                )}
            </div>

            {currentEmail && (
                <div className="mt-4 space-y-4 pt-4 border-t border-[#e5e7eb]">
                    {!isEditing && satisfactionChoice === null && (
                        <div className="p-4 text-center bg-[#f8fafc] rounded-lg">
                            <h3 className="font-semibold mb-3 text-[#111827]">Are you satisfied with this draft?</h3>
                            <div className="flex justify-center items-center space-x-4">
                                <IconButton onClick={() => setSatisfactionChoice('unsatisfied')} className="text-red-500 hover:bg-red-100" title="Unsatisfied"><ThumbsDown size={24} /></IconButton>
                                <IconButton onClick={() => setSatisfactionChoice('satisfied')} className="text-[#16a34a] hover:bg-green-100" title="Satisfied"><ThumbsUp size={24} /></IconButton>
                            </div>
                        </div>
                    )}

                    {!isEditing && satisfactionChoice === 'unsatisfied' && (
                        <div className="p-4 text-center bg-[#f8fafc] rounded-lg space-y-4">
                             <h3 className="font-semibold text-[#111827]">What needs to be changed?</h3>
                             <div className="flex justify-center items-center space-x-3">
                                <button onClick={() => { setSatisfactionChoice(null); setShowRegenerateInput(false); }} className="font-semibold text-[#6b7280] px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">Back</button>
                                <button onClick={() => setShowRegenerateInput(true)} className="font-semibold text-[#111827] px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">Regenerate (for major changes)</button>
                                <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-[#16a34a] px-4 py-2 rounded-lg hover:bg-green-100 transition-colors"><Edit size={18} />Edit Manually (for minor fixes)</button>
                             </div>
                             {showRegenerateInput && (
                                <div className="flex space-x-2 pt-3">
                                    <input type="text" value={feedback} onChange={(e) => setFeedback(e.target.value)} placeholder="e.g., 'Make it more formal'" className="flex-grow px-3 py-2 bg-white border border-[#e5e7eb] rounded-md shadow-sm focus:outline-none focus:ring-[#16a34a] focus:border-[#16a34a] sm:text-sm" />
                                    <PrimaryButton onClick={handleRegenerateWithFeedback} disabled={!feedback || isRegenerating || isLoading} isLoading={isRegenerating} className="w-auto px-4"><RefreshCw size={16} /></PrimaryButton>
                                </div>
                             )}
                        </div>
                    )}

                    {!isEditing && satisfactionChoice === 'satisfied' && (
                        <div className="flex items-center justify-end space-x-3">
                             <button onClick={() => setSatisfactionChoice(null)} className="font-semibold text-[#6b7280] px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">Back</button>
                            <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-[#111827] px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"><Edit size={18} />Edit</button>
                            <PrimaryButton onClick={handleApprove} disabled={isLoading} isLoading={isLoading && !!currentEmail}><Send size={16} className="mr-2" />Approve & Send</PrimaryButton>
                        </div>
                    )}

                    {isEditing && (
                        <div className="flex items-center justify-end">
                             <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-[#16a34a] px-4 py-2 rounded-lg hover:bg-green-100 transition-colors"><Check size={18} />Save & Continue</button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default EmailDisplay;
