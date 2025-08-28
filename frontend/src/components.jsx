import React from 'react';
import { RefreshCw } from 'lucide-react';

// --- Form Input Components ---

export const InputField = ({ id, label, value, onChange, disabled = false }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-[#111827]-700 mb-1">{label}</label>
        <input
            type="text"
            id={id}
            value={value}
            onChange={onChange}
            disabled={disabled}
            className="w-full px-3 py-2 bg-white border border-[#e5e7eb] rounded-lg shadow-sm focus:outline-none focus:ring-[#16a34a] focus:border-[#16a34a] sm:text-sm transition-shadow disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
    </div>
);

export const TextareaField = ({ id, label, value, onChange, placeholder }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-[#111827] mb-1">{label}</label>
        <textarea
            id={id}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            rows="3"
            className="w-full px-3 py-2 bg-white border border-[#e5e7eb] rounded-lg shadow-sm focus:outline-none focus:ring-[#16a34a] focus:border-[#16a34a] sm:text-sm transition-shadow disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
    </div>
);

// --- Button Components ---

export const IconButton = ({ onClick, children, disabled = false, className = '', title = '' }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        title={title}
        className={`p-2 rounded-full hover:bg-gray-200 disabled:bg-transparent disabled:text-gray-300 disabled:cursor-not-allowed transition-colors ${className}`}
    >
        {children}
    </button>
);

export const PrimaryButton = ({ onClick, children, disabled = false, isLoading = false, className = '', title = '' }) => (
    <button
        onClick={onClick}
        disabled={disabled || isLoading}
        title={title}
        className={`w-full flex justify-center items-center bg-[#16a34a] text-white font-semibold py-2 px-4 rounded-lg hover:bg-[#15803d] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#16a34a] transition duration-150 ease-in-out disabled:bg-[#4ade80] disabled:cursor-not-allowed ${className}`}
    >
        {isLoading ? <RefreshCw className="animate-spin h-5 w-5" /> : children}
    </button>
);

// --- Data Display Component ---

export const DataCard = ({ title, data }) => (
    <details className="bg-[#f8fafc] p-3 rounded-lg border border-[#e5e7eb]">
        <summary className="font-semibold text-[#111827] cursor-pointer">{title}</summary>
        <div className="mt-2 text-xs text-[#6b7280]">
            <pre className="bg-gray-100 p-2 rounded whitespace-pre-wrap break-all">{JSON.stringify(data, null, 2)}</pre>
        </div>
    </details>
);

// --- Notification Component ---

export const Notification = ({ message, type, show }) => {
    if (!show) return null;

    const baseClasses = 'fixed bottom-5 right-5 p-4 rounded-lg shadow-xl text-white transition-transform transform animate-bounce';
    const typeClasses = {
        success: 'bg-[#16a34a]', // Primary Green
        info: 'bg-[#10b981]',    // Secondary Green
        error: 'bg-red-500',
    };

    return (
        <div className={`${baseClasses} ${typeClasses[type] || 'bg-red-500'}`}>
            {message}
        </div>
    );
};
