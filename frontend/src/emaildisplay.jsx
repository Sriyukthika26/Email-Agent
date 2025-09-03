import React, { useState, useEffect } from 'react';
import { 
    ArrowLeft, ArrowRight, Edit, Check, Send, RefreshCw, 
    ThumbsUp, ThumbsDown, Bold, Italic, List, ListOrdered, Undo 
} from 'lucide-react';
import { IconButton, PrimaryButton } from './components';

// Tiptap Imports
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';

// --- TIPTAP EDITOR COMPONENTS ---

const TiptapStyleFix = () => (
    <style>{`
    /* Editor container fixes */
    .tiptap .ProseMirror {
        outline: none !important;
        padding: 12px !important;
        min-height: 200px;
        max-height: 400px;
        overflow-y: auto;
    }
    .subject-editor .ProseMirror {
        min-height: auto !important;
        max-height: 60px !important;
        padding: 8px 12px !important;
        border: none !important;
    }
    /* List styling fixes for BOTH editor and display view */
    .tiptap .ProseMirror ul, .email-content ul {
        list-style-type: disc !important;
        margin-left: 0 !important;
        padding-left: 24px !important;
    }
    .tiptap .ProseMirror ol, .email-content ol {
        list-style-type: decimal !important;
        margin-left: 0 !important;
        padding-left: 24px !important;
    }
    .tiptap .ProseMirror ul li, .tiptap .ProseMirror ol li, .email-content ul li, .email-content ol li {
        display: list-item !important;
        margin-bottom: 4px;
        padding-left: 4px;
    }
    .tiptap .ProseMirror ul li::marker, .tiptap .ProseMirror ol li::marker, .email-content ul li::marker, .email-content ol li::marker {
        color: #374151;
    }
    /* Nested lists for BOTH editor and display view */
    .tiptap .ProseMirror ul ul, .tiptap .ProseMirror ol ol, .tiptap .ProseMirror ul ol, .tiptap .ProseMirror ol ul, .email-content ul ul, .email-content ol ol, .email-content ul ol, .email-content ol ul {
        margin-top: 4px;
        margin-bottom: 4px;
    }
    .ProseMirror-focused {
        outline: 2px solid #16a34a !important;
        outline-offset: -2px;
    }
    /* Placeholder styles */
    .tiptap p.is-editor-empty:first-child::before, .subject-editor .ProseMirror p.is-editor-empty:first-child::before {
        color: #9ca3af;
        content: attr(data-placeholder);
        float: left;
        height: 0;
        pointer-events: none;
        font-style: italic;
    }
    .tiptap .ProseMirror p {
        margin-bottom: 8px;
    }
    .tiptap .ProseMirror p:last-child {
        margin-bottom: 0;
    }
    `}</style>
);

const TiptapToolbar = ({ editor }) => {
    if (!editor) return null;
    return (
        <div className="border-b border-gray-300 p-2 flex items-center space-x-1 bg-gray-50 rounded-t-lg">
            <IconButton onClick={() => editor.chain().focus().toggleBold().run()} disabled={!editor.can().chain().focus().toggleBold().run()} className={`${editor.isActive('bold') ? 'bg-[#16a34a] text-white' : 'hover:bg-gray-200'} transition-colors`} title="Bold"><Bold size={16} /></IconButton>
            <IconButton onClick={() => editor.chain().focus().toggleItalic().run()} disabled={!editor.can().chain().focus().toggleItalic().run()} className={`${editor.isActive('italic') ? 'bg-[#16a34a] text-white' : 'hover:bg-gray-200'} transition-colors`} title="Italic"><Italic size={16} /></IconButton>
            <IconButton onClick={() => editor.chain().focus().toggleBulletList().run()} className={`${editor.isActive('bulletList') ? 'bg-[#16a34a] text-white' : 'hover:bg-gray-200'} transition-colors`} title="Bullet List"><List size={16} /></IconButton>
            <IconButton onClick={() => editor.chain().focus().toggleOrderedList().run()} className={`${editor.isActive('orderedList') ? 'bg-[#16a34a] text-white' : 'hover:bg-gray-200'} transition-colors`} title="Numbered List"><ListOrdered size={16} /></IconButton>
            <IconButton onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().chain().focus().undo().run()} className="hover:bg-gray-200 transition-colors" title="Undo"><Undo size={16} /></IconButton>
        </div>
    );
};

const EditorField = ({ title, editor, containerClassName = '', editorClassName = '' }) => (
    <div className={`bg-white rounded-lg border border-gray-300 shadow-sm ${containerClassName}`}>
        <div className="px-3 py-2 border-b border-gray-200 bg-gray-50 rounded-t-lg">
            <span className="text-sm font-medium text-gray-600">{title}:</span>
        </div>
        <EditorContent editor={editor} className={editorClassName}/>
    </div>
);

// Define shared Tiptap extensions configuration
const tiptapExtensions = [
    StarterKit.configure({
        bulletList: { HTMLAttributes: { class: 'tiptap-bullet-list' } },
        orderedList: { HTMLAttributes: { class: 'tiptap-ordered-list' } },
    }),
    Placeholder, // Will be configured per-instance
];


// --- Main Display Component ---
const EmailDisplay = ({
    emailHistory, historyIndex, isLoading, isRegenerating, isEditing,
    editedEmail, setEditedEmail, feedback, setFeedback, navigateHistory,
    handleEditToggle, handleRegenerateWithFeedback, handleApprove,
    satisfactionChoice, setSatisfactionChoice, handleCancelEdit
}) => {
    const currentEmail = historyIndex >= 0 ? emailHistory[historyIndex] : null;
    const [showRegenerateInput, setShowRegenerateInput] = React.useState(false);
    const [activeEditor, setActiveEditor] = useState(null);

    const subjectEditor = useEditor({
        extensions: tiptapExtensions.map(ext =>
            ext.name === 'placeholder' ? Placeholder.configure({ placeholder: 'Email Subject' }) : ext
        ),
        content: editedEmail.subject,
        onUpdate: ({ editor }) => {
            const html = editor.getHTML();
            setEditedEmail(prev => ({ ...prev, subject: html === '<p></p>' ? '' : html.replace(/^<p>(.*)<\/p>$/, '$1') }));
        },
        onFocus: () => setActiveEditor('subject'),
        editorProps: { attributes: { class: 'prose prose-sm focus:outline-none' } },
    });

    const bodyEditor = useEditor({
        extensions: tiptapExtensions.map(ext =>
            ext.name === 'placeholder' ? Placeholder.configure({ placeholder: 'Write your email body here...' }) : ext
        ),
        content: editedEmail.body,
        onUpdate: ({ editor }) => setEditedEmail(prev => ({ ...prev, body: editor.getHTML() })),
        onFocus: () => setActiveEditor('body'),
        editorProps: { attributes: { class: 'prose prose-sm focus:outline-none max-w-none' } },
    });
    
    useEffect(() => {
        if (isEditing && currentEmail) {
            if (subjectEditor) {
                const currentSubjectHTML = subjectEditor.getHTML();
                const expectedSubjectHTML = editedEmail.subject || '';
                if (currentSubjectHTML !== expectedSubjectHTML && currentSubjectHTML !== `<p>${expectedSubjectHTML}</p>`) {
                    subjectEditor.commands.setContent(expectedSubjectHTML);
                }
            }
            if (bodyEditor) {
                const currentBodyHTML = bodyEditor.getHTML();
                const expectedBodyHTML = editedEmail.body || '';
                if (currentBodyHTML !== expectedBodyHTML) {
                    bodyEditor.commands.setContent(expectedBodyHTML);
                }
            }
        }
    }, [isEditing, editedEmail.subject, editedEmail.body, subjectEditor, bodyEditor, currentEmail]);

    useEffect(() => {
        setSatisfactionChoice(null);
        setShowRegenerateInput(false);
    }, [historyIndex, setSatisfactionChoice]);

    const getActiveEditorInstance = () => activeEditor === 'subject' ? subjectEditor : bodyEditor;

    return (
        <div className="lg:col-span-3 bg-white p-6 shadow-lg rounded-xl border border-[#e5e7eb]">
            <TiptapStyleFix />
            <div className="flex justify-between items-center mb-4 border-b border-[#e5e7eb] pb-3">
                <h2 className="text-xl font-semibold text-[#111827]">Generated Email</h2>
                {emailHistory.length > 0 && !isEditing && (
                    <div className="flex items-center space-x-2">
                        <IconButton onClick={() => navigateHistory(-1)} disabled={historyIndex <= 0}><ArrowLeft size={20} /></IconButton>
                        <span className="text-sm font-medium text-[#6b7280] tabular-nums">{historyIndex + 1} / {emailHistory.length}</span>
                        <IconButton onClick={() => navigateHistory(1)} disabled={historyIndex >= emailHistory.length - 1}><ArrowRight size={20} /></IconButton>
                    </div>
                )}
            </div>

            <div className="min-h-[400px] border border-[#e5e7eb] rounded-lg bg-[#f8fafc] p-4 flex flex-col">
                {isLoading && !currentEmail ? (
                    <div className="flex-grow flex items-center justify-center"><RefreshCw className="h-10 w-10 text-[#16a34a] animate-spin" /></div>
                ) : currentEmail ? (
                    <div className="flex-grow flex flex-col">
                        {isEditing ? (
                            <div className="flex flex-col h-full space-y-4">
                                <TiptapToolbar editor={getActiveEditorInstance()} />
                                <EditorField title="Subject" editor={subjectEditor} editorClassName="subject-editor" />
                                <EditorField title="Body" editor={bodyEditor} containerClassName="flex-grow flex flex-col" editorClassName="tiptap flex-grow" />
                            </div>
                        ) : (
                            <>
                                <h3 className="text-lg font-semibold pb-2 border-b border-[#e5e7eb] email-content" dangerouslySetInnerHTML={{ __html: currentEmail.subject }} />
                                <div className="email-content prose prose-sm max-w-none flex-grow text-[#111827] leading-relaxed pt-4" dangerouslySetInnerHTML={{ __html: currentEmail.body }} />
                            </>
                        )}
                    </div>
                ) : (
                    <div className="flex-grow flex items-center justify-center text-[#6b7280]">Click "Generate Email" to start.</div>
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
                        <div className="flex items-center justify-end space-x-3">
                            <button onClick={handleCancelEdit} className="font-semibold text-[#6b7280] px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">Cancel</button>
                            <button onClick={handleEditToggle} className="flex items-center gap-2 font-semibold text-white bg-[#16a34a] px-4 py-2 rounded-lg hover:bg-[#15803d] transition-colors"><Check size={18} />Save & Continue</button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default EmailDisplay;