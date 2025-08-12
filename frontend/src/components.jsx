import React from 'react';
import { RefreshCw } from 'lucide-react';

// --- Form Input Components ---

export const InputField = ({ id, label, value, onChange }) => (
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

export const TextareaField = ({ id, label, value, onChange, placeholder }) => (
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

// --- Button Components ---

export const IconButton = ({ onClick, children, disabled = false, className = '' }) => (
    <button
        onClick={onClick}
        disabled={disabled}
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
        className={`w-full flex justify-center items-center bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out disabled:bg-indigo-300 disabled:cursor-not-allowed ${className}`}
    >
        {isLoading ? <RefreshCw className="animate-spin h-5 w-5" /> : children}
    </button>
);

// --- Data Display Component ---

export const DataCard = ({ title, data }) => (
    <details className="bg-gray-50 p-3 rounded-lg border border-gray-200">
        <summary className="font-semibold text-gray-800 cursor-pointer">{title}</summary>
        <div className="mt-2 text-xs text-gray-600">
            <pre className="bg-gray-100 p-2 rounded whitespace-pre-wrap break-all">{JSON.stringify(data, null, 2)}</pre>
        </div>
    </details>
);

// --- Notification Component ---

export const Notification = ({ message, type, show }) => {
    if (!show) return null;

    const baseClasses = 'fixed bottom-5 right-5 p-4 rounded-lg shadow-xl text-white transition-transform transform animate-bounce';
    const typeClasses = {
        success: 'bg-green-500',
        info: 'bg-blue-500',
        error: 'bg-red-500',
    };

    return (
        <div className={`${baseClasses} ${typeClasses[type] || 'bg-red-500'}`}>
            {message}
        </div>
    );
};
